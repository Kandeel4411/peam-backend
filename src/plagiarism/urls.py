from django.urls import path, include

from .views import ProjectPlagiarismView, ProjectPlagiarismCompareView

# Project plagiarism patterns
project_plagiarism_pattern = "plagiarism/"
project_plagiarism_compare_pattern = f"{project_plagiarism_pattern}compare/"

urlpatterns = [
    path(project_plagiarism_pattern, ProjectPlagiarismView.as_view(), name="project-plagiarism"),
    path(project_plagiarism_compare_pattern, ProjectPlagiarismCompareView.as_view(), name="project-plagiarism-compare"),
]
