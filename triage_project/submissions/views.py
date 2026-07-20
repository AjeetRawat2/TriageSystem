import json
import csv
import os
import httpx
from datetime import datetime, timezone

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count
from django.core.paginator import Paginator
from .models import ProjectSubmission

# Import AsyncGroq to safely handle non-blocking LLM calls
from groq import AsyncGroq

# Initialize the Groq client securely using environment variables
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# Set this to the exact date your event started to check for cheating
HACKATHON_START_DATE = datetime(2026, 7, 10, 18, 0, tzinfo=timezone.utc)


# ==========================================
# TRIAGE DASHBOARD VIEWS
# ==========================================

def dashboard(request):
    """Renders the main triage dashboard with paginated projects and chart analytics."""
    project_list = ProjectSubmission.objects.all().order_by('-id')
    paginator = Paginator(project_list, 50) # Show 50 projects per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate At-a-Glance Analytics
    total_projects = ProjectSubmission.objects.count()
    reviewed_count = ProjectSubmission.objects.filter(is_reviewed=True).count()
    pending_count = total_projects - reviewed_count
    
    # Get the distribution of predicted tracks for Chart.js
    track_distribution = ProjectSubmission.objects.values('predicted_track').annotate(count=Count('predicted_track')).order_by('-count')

    chart_labels = [item['predicted_track'] for item in track_distribution if item['predicted_track']]
    chart_data = [item['count'] for item in track_distribution if item['predicted_track']]

    context = {
        'projects': page_obj,
        'total_projects': total_projects,
        'reviewed_count': reviewed_count,
        'pending_count': pending_count,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
    }
    
    return render(request, 'submissions/dashboard.html', context)


@require_POST
def approve_project(request, project_id):
    """Marks a project as manually verified and routed."""
    try:
        project = ProjectSubmission.objects.get(id=project_id)
        project.is_reviewed = True
        project.save()
        return JsonResponse({'status': 'success'})
    except ProjectSubmission.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Project not found'}, status=404)

@require_POST
def override_project(request, project_id):
    """Updates a project's track based on manual organizer override."""
    try:
        data = json.loads(request.body)
        new_track = data.get('new_track')
        project = ProjectSubmission.objects.get(id=project_id)
        project.predicted_track = new_track
        project.save()
        return JsonResponse({'status': 'success', 'new_track': new_track})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
async def ask_groq_summary(request, project_id):
    """Async view that asks Groq to explain why the ML model picked a specific track."""
    try:
        project = await ProjectSubmission.objects.aget(id=project_id)
        completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a hackathon triage assistant. Explain in 2 sentences why this project belongs in the track it was assigned to based on the description."
                },
                {
                    "role": "user",
                    "content": f"Track: {project.predicted_track}\nDescription: {project.abstract}"
                }
            ],
            model="llama-3.1-8b-instant",
        )
        summary = completion.choices[0].message.content
        return JsonResponse({'status': 'success', 'summary': summary})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
async def validate_repo(request, project_id):
    """On-demand GitHub API check for repository commit dates. Now supports manual link saving!"""
    try:
        data = json.loads(request.body)
        new_url = data.get('github_url', '').strip()
        
        project = await ProjectSubmission.objects.aget(id=project_id)
        
        # If the organizer typed a new link, save it to the DB instantly!
        if new_url and new_url != project.github_url:
            project.github_url = new_url
            await project.asave()
            
        github_url = project.github_url
        
        if not github_url or "github.com" not in github_url:
            return JsonResponse({'status': 'error', 'message': 'Invalid or missing GitHub URL'})
            
        # Extract the repo path from the full URL
        repo_path = github_url.replace("https://github.com/", "").strip("/")
        
        async with httpx.AsyncClient() as http_client:
            commits_url = f"https://api.github.com/repos/{repo_path}/commits"
            res = await http_client.get(commits_url, headers={"Accept": "application/vnd.github.v3+json"})
            
            if res.status_code == 200:
                commits = res.json()
                if not commits:
                    return JsonResponse({'status': 'error', 'message': 'No commits found.'})
                    
                # Get the date of the very FIRST commit (last item in the array)
                first_commit_date_str = commits[-1]['commit']['author']['date']
                first_commit_date = datetime.fromisoformat(first_commit_date_str.replace("Z", "+00:00"))
                
                # Compare dates to ensure they didn't start coding before the event
                if first_commit_date < HACKATHON_START_DATE:
                    return JsonResponse({'status': 'success', 'type': 'fail', 'message': '⚠️ COMMITTED BEFORE THE EVENT'})
                else:
                    return JsonResponse({'status': 'success', 'type': 'pass', 'message': '✅ COMMITTED AFTER THE EVENT'})
            else:
                return JsonResponse({'status': 'error', 'message': 'GitHub API limit reached or repo not found.'})
                
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==========================================
# JUDGE PORTAL VIEWS
# ==========================================

def judge_dashboard(request):
    """Renders the judge portal showing only approved projects."""
    projects = ProjectSubmission.objects.filter(is_reviewed=True).order_by('-id')
    context = {
        'projects': projects,
    }
    return render(request, 'submissions/judge_dashboard.html', context)

@require_POST
def submit_score(request, project_id):
    """Saves the manual score given by the judge."""
    try:
        data = json.loads(request.body)
        score = int(data.get('score', 0))
        project = ProjectSubmission.objects.get(id=project_id)
        project.score = score
        project.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
async def judge_evaluate_project(request, project_id):
    """Provides an AI evaluation of strengths and weaknesses for the judge."""
    try:
        project = await ProjectSubmission.objects.aget(id=project_id)
        
        completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Hackathon Judge Co-Pilot. Read this project abstract and quickly summarize 1 core strength and 1 potential weakness or area of concern to help a human judge grade it."
                },
                {"role": "user", "content": f"Title: {project.title}\nDescription: {project.abstract}"}
            ],
            model="llama-3.1-8b-instant",
        )
        return JsonResponse({'status': 'success', 'summary': completion.choices[0].message.content})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_GET
async def export_winners_csv(request):
    """Generates a CSV of top-scoring projects with AI-written award justifications."""
    try:
        # Grab the top 10 highest-scored projects
        top_projects = []
        async for p in ProjectSubmission.objects.filter(is_reviewed=True, score__gt=0).order_by('-score')[:10]:
            top_projects.append(p)
            
        if not top_projects:
            return HttpResponse("No projects have been scored yet. Please grade some projects first.", status=400)

        # Prompt AI to write a justification for each project using JSON mode
        prompt_data = "Here are the top hackathon projects:\n\n"
        for p in top_projects:
            prompt_data += f"Title: {p.title}\nAbstract: {p.abstract[:200]}...\n\n"
            
        prompt_data += "Write a 1-sentence celebratory award justification for why each project won. You MUST return ONLY a valid JSON object where the keys are the exact Project Titles, and the values are your 1-sentence justifications."

        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a hackathon judge. Output strictly in JSON."},
                {"role": "user", "content": prompt_data}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"} 
        )
        
        # Parse the AI's JSON response
        ai_justifications = json.loads(completion.choices[0].message.content)

        # Build and return the CSV file
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="hackathon_winners.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Rank', 'Project Title', 'Track', 'Score', 'AI Award Justification'])
        
        for idx, p in enumerate(top_projects, start=1):
            ai_note = ai_justifications.get(p.title, "Awarded for outstanding technical achievement.")
            writer.writerow([idx, p.title, p.predicted_track, p.score, ai_note])
            
        return response

    except Exception as e:
        return HttpResponse(f"Error generating CSV: {str(e)}", status=500)