import pandas as pd
import joblib
import os
from django.core.management.base import BaseCommand
from submissions.models import ProjectSubmission

class Command(BaseCommand):
    help = 'Imports hackathon projects from CSV and predicts tracks using the ML model'

    def handle(self, *args, **kwargs):
        # 1. Define file paths (assuming they are next to manage.py)
        csv_file = 'devpost_raw_5k.csv'  
        model_file = 'hackathon_model.pkl'

        # Safety check
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"Could not find {csv_file}! Place it next to manage.py"))
            return
        if not os.path.exists(model_file):
            self.stdout.write(self.style.ERROR(f"Could not find {model_file}! Place it next to manage.py"))
            return

        self.stdout.write("Loading ML Model...")
        model = joblib.load(model_file)
        
        self.stdout.write(f"Loading data from {csv_file}...")
        df = pd.read_csv(csv_file)

        # Optional: Limit to first 500 for testing so it doesn't take forever
        # df = df.head(500) 

        self.stdout.write(f"Importing {len(df)} projects. This might take a minute...")

        # 2. Loop through the dataframe and create database records
        created_count = 0
        for index, row in df.iterrows():
            # Handle potential NaN values in the abstract
            abstract_text = str(row['full_desc']) if pd.notna(row['full_desc']) else "No description provided."
            
            # Get prediction from model (returns an array, so grab the first item)
            pred_track = model.predict([abstract_text])[0]
            
            # Optional: If your model outputs probabilities, you could grab the confidence score
            # probabilities = model.predict_proba([abstract_text])[0]
            # confidence = max(probabilities)
            
            # Save to Database
            ProjectSubmission.objects.create(
                title=row['title'],
                abstract=abstract_text,
                predicted_track=pred_track,
                # confidence_score=confidence  # Uncomment if you used predict_proba
            )
            
            created_count += 1
            if created_count % 100 == 0:
                self.stdout.write(f"  ...imported {created_count} records")

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {created_count} projects!'))