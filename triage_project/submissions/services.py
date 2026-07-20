import httpx
import base64
import json
from datetime import datetime, timezone

# We will pretend the hackathon started on Friday at 6:00 PM
HACKATHON_START_DATE = datetime(2026, 7, 10, 18, 0, tzinfo=timezone.utc)

async def analyze_github_repo(github_url):
    """Fetches commit history and tech stack from GitHub API."""
    if not github_url or "github.com" not in github_url:
        return {"status": "invalid_url", "stack": []}

    # Convert "https://github.com/AjeetRawat2/MyDjangoTweet" to "AjeetRawat2/MyDjangoTweet"
    repo_path = github_url.replace("https://github.com/", "").strip("/")
    
    # We use httpx for async HTTP requests
    async with httpx.AsyncClient() as client:
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # 1. CHECK COMMIT TIMESTAMPS
        commits_url = f"https://api.github.com/repos/{repo_path}/commits"
        commits_res = await client.get(commits_url, headers=headers)
        
        status = "valid"
        if commits_res.status_code == 200:
            commits = commits_res.json()
            if commits:
                # Get the date of the very first commit (last in the list)
                first_commit_date_str = commits[-1]['commit']['author']['date']
                first_commit_date = datetime.fromisoformat(first_commit_date_str.replace("Z", "+00:00"))
                
                # If they started coding before the hackathon began -> flag them!
                if first_commit_date < HACKATHON_START_DATE:
                    status = "warning_old_commits"
        
        # 2. EXTRACT TECH STACK (Look for package.json)
        stack = []
        pkg_url = f"https://api.github.com/repos/{repo_path}/contents/package.json"
        pkg_res = await client.get(pkg_url, headers=headers)
        
        if pkg_res.status_code == 200:
            file_data = pkg_res.json()
            # GitHub sends file contents encoded in Base64
            decoded_content = base64.b64decode(file_data['content']).decode('utf-8')
            try:
                package_json = json.loads(decoded_content)
                dependencies = package_json.get('dependencies', {})
                # Extract the top 5 dependencies as the tech stack
                stack = list(dependencies.keys())[:5] 
            except json.JSONDecodeError:
                pass

        return {"status": status, "stack": stack}