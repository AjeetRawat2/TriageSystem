import os
import django
import csv
import time
import re
from asgiref.sync import async_to_sync

# 1. Setup the Django Environment so we can use our Database Models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_triage.settings')
django.setup()

from submissions.models import ProjectSubmission
from submissions.services import analyze_github_repo

def clean_html(text):
    """Cleans the raw HTML abstract from Devpost."""
    if not text: 
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def run_import():
    print("🧹 Clearing old database records...")
    ProjectSubmission.objects.all().delete()
    
    csv_file = "devpost_raw_5k.csv"
    
    print(f"📂 Opening {csv_file}...")
    
    try:
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for index, row in enumerate(reader):
                # STOP AFTER 50: Keeps the demo fast and avoids GitHub API bans
                # if index >= 50:
                #     print("\n🛑 Reached 50 projects. Stopping import for demo purposes!")
                #     break
                    
                title = row.get('title', 'Unknown Title')
                raw_abstract = row.get('full_desc', '')
                abstract = clean_html(raw_abstract)
                
                # --- FETCH LINKS FROM CSV ---
                # Make sure these match the exact column headers in your CSV!
                project_link = row.get('project_link', '') 
                github_url = row.get('github_url', '')
                
                status = 'pending'
                tech_stack = []

                # --- AUTO-VALIDATE GITHUB IF IT EXISTS ---
                if github_url and 'github.com' in github_url:
                    print(f"[{index + 1}/50] 🔍 Validating GitHub for: {title[:30]}...")
                    try:
                        analysis = async_to_sync(analyze_github_repo)(github_url)
                        status = analysis['status']
                        tech_stack = analysis['stack']
                    except Exception as e:
                        print(f"  -> ❌ Error reaching GitHub: {e}")
                    
                    # Pause for 0.5 seconds to respect GitHub API limits
                    time.sleep(0.5)
                else:
                    print(f"[{index + 1}/50] 📥 Importing: {title[:30]} (No GitHub Link)")

                # --- SAVE TO DATABASE ---
                ProjectSubmission.objects.create(
                    title=title,
                    abstract=abstract,
                    project_link=project_link,
                    github_url=github_url,
                    github_status=status,
                    tech_stack=tech_stack
                )
                
        print("\n✅ Import complete!")
        print("🤖 Don't forget to run 'python run_predictions.py' next to add the ML Tracks!")
        
    except FileNotFoundError:
        print(f"❌ Error: {csv_file} not found. Make sure it is in the same folder as this script.")

if __name__ == '__main__':
    run_import()