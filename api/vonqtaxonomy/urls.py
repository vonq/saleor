from django.urls import path

from . import views

app_name = "vonqtaxonomy"

urlpatterns = [
    path("industry", views.get_industry_mapping, name="industry"),
    path("job-category", views.get_job_category_mapping, name="job-category"),
]
