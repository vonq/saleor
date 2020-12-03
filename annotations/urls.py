from django.conf.urls import url
from django.urls import path

from api.annotations import views

app_name = "annotations"

urlpatterns = [
    path("", views.index, name="index"),
    path("product-annotation", views.product_annotation, name="product_annotation"),
    path("title-annotation", views.titles_annotation, name="titles_annotation"),
    path(
        "job-title-translation",
        views.job_title_translation,
        name="job_title_translation",
    ),
    path("dashboard", views.dashboard, name="dashboard"),
    path("get-titles", views.get_job_titles_json, name="get_job_titles_json"),
    path("locations", views.get_locations_json, name="get_locations_json"),
    path("job-functions", views.get_job_functions_json, name="get_job_functions_json"),
    path(
        "get-products-text", views.get_products_text_json, name="get_products_text_json"
    ),
    path("get-product/<int:id>", views.get_product_json, name="get_product_json"),
    path("get-boards", views.get_boards, name="get_boards"),
    path("update-title", views.update_title, name="update_title"),
    path("add-categorisation", views.add_categorisation, name="add_categorisation"),
    path("set-category-values", views.set_category_values, name="set_category_values"),
    path("set-locations", views.set_locations, name="set_locations"),
    path("export-options", views.export_options_json, name="export_options_json"),
    path(
        "export-categories-csv",
        views.export_categories_csv,
        name="export_categories_csv",
    ),
]
