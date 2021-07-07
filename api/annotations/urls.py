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
    path("channel-annotation", views.channel_annotation, name="channel_annotation"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("search-relevancy", views.search_relevancy, name="search_relevancy"),
    path(
        "posting-requirements", views.posting_requirements, name="posting_requirements"
    ),
    path("get-titles", views.get_job_titles_json, name="get_job_titles_json"),
    path("locations", views.get_locations_json, name="get_locations_json"),
    path("job-functions", views.get_job_functions_json, name="get_job_functions_json"),
    path(
        "get-products-text", views.get_products_text_json, name="get_products_text_json"
    ),
    path("get-product/<int:id>", views.get_product_json, name="get_product_json"),
    path("get-products", views.get_products, name="get_products"),
    path("get-channels", views.get_channel_list_json, name="get_channel_list"),
    path("get-channel/<int:channel_id>", views.get_channel_json, name="get_channel"),
    path("update-title", views.update_title, name="update_title"),
    path("add-categorisation", views.add_categorisation, name="add_categorisation"),
    path("set-category-values", views.set_category_values, name="set_category_values"),
    path(
        "migrate-industry-to-category",
        views.migrate_industry_to_category,
        name="migrate_industry_to_category",
    ),
    path("set-locations", views.set_locations, name="set_locations"),
    path("set-channel", views.set_channel, name="set_channel"),
    path(
        "set-posting-requirements",
        views.set_posting_requirements,
        name="set_posting_requirements",
    ),
    path(
        "reference_product_search",
        views.reference_product_search,
        name="reference_product_search",
    ),
    path("export-options", views.export_options_json, name="export_options_json"),
    path(
        "export-categories-csv",
        views.export_categories_csv,
        name="export_categories_csv",
    ),
    path("parse-title", views.parse_title, name="parse_title"),
    path(
        "parse-title-testbench",
        views.parse_title_testbench,
        name="parse_title_testbench",
    ),
    path(
        "headline-parsing-checker",
        views.parse_headline_checker,
        name="parse_headline_checker",
    ),
]
