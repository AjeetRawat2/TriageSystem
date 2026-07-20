import os
import django
import joblib
import re

# 1. Setup the Django Environment so we can use our Database Models
# (Assuming your main Django project folder is named 'hackathon_triage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_triage.settings')
django.setup()

from submissions.models import ProjectSubmission

def clean_html(text):
    """Replicates the exact text cleaning we used during model training."""
    if not text: 
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def run_triage():
    print("🤖 Loading LinearSVC Model...")
    try:
        model = joblib.load("hackathon_model.pkl")
    except FileNotFoundError:
        print("❌ Error: hackathon_model.pkl not found! Make sure it is in the same folder as this script.")
        return

    # Fetch all projects to re-classify them with the new, smarter model
    projects = ProjectSubmission.objects.all()
    total_projects = projects.count()
    
    if total_projects == 0:
        print("⚠️ No projects found in the database. Run your Devpost import script first!")
        return

    print(f"🚀 Predicting tracks for {total_projects} projects...")
    
    updated_count = 0
    for project in projects:
        # Clean the abstract so the model understands it
        cleaned_text = clean_html(project.abstract)
        
        # The model expects a list/array of strings, even for a single prediction
        prediction = model.predict([cleaned_text])[0]
        
        # Update the database
        project.predicted_track = prediction
        
        # Note: LinearSVC doesn't output standard probability percentages natively, 
        # so we will set a placeholder confidence score here.
        project.confidence_score = 0.82 
        project.save()
        
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"⚙️ Processed {updated_count} / {total_projects} projects...")

    print(f"\n✅ Triage Complete! Successfully routed {updated_count} projects using the new 82% accuracy ML model.")

if __name__ == "__main__":
    run_triage()