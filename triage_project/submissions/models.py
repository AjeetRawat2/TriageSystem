from django.db import models

class ProjectSubmission(models.Model):
    """
    Represents a raw project submission scraped from Devpost.
    """
    # Core Devpost Data
    title = models.CharField(max_length=255)
    project_link = models.URLField(max_length=500, blank=True, null=True)
    abstract = models.TextField(help_text="The raw or cleaned project description.")
    
    # --- GITHUB FIELDS ---
    github_url = models.URLField(blank=True, null=True)
    github_status = models.CharField(max_length=50, default='pending')
    tech_stack = models.JSONField(default=list, blank=True)
    
    # The 'ground truth' track you generated during EDA
    target_track = models.CharField(max_length=100, blank=True, null=True)

    # ML Predictions (Populated later by the model)
    predicted_track = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(default=0.0, help_text="How confident the ML model is (0.0 to 1.0)")
    
    # Review Status
    is_reviewed = models.BooleanField(default=False, help_text="Has an organizer manually verified this?")
    
    # Judge Score
    score = models.IntegerField(default=0, help_text="Manual score given by the judge (0-100)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title