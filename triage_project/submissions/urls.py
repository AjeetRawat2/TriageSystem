from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('approve/<int:project_id>/', views.approve_project, name='approve_project'),
    path('override/<int:project_id>/', views.override_project, name='override_project'),
    path('summary/<int:project_id>/', views.ask_groq_summary, name='summary'),
    path('validate-repo/<int:project_id>/', views.validate_repo, name='validate_repo'),
    
    # --- JUDGE PORTAL ROUTES ---
    path('judge/', views.judge_dashboard, name='judge_dashboard'),
    path("login/", views.login_view, name="login"),
    path('rate/<int:project_id>/', views.submit_score, name='submit_score'),
    path('judge_summary/<int:project_id>/', views.judge_evaluate_project, name='judge_summary'),
    path('export-winners/', views.export_winners_csv, name='export_winners_csv'),
]
