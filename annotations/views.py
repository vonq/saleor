from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import (
    permission_required,
    user_passes_test,
)

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

from api.products.models import Industry, Product, JobFunction, JobTitle, Location

import json
import csv


def index(request):
    return HttpResponse("left intentionally blank")


def product_annotation(request):
    industries = Industry.objects.all()
    jobFunctions = JobFunction.objects.all()
    return render(
        request,
        "product_annotation.html",
        {
            "industries": list(industries.values("name")),
            "jobFunctions": list(jobFunctions.values("name")),
            "channelTypes": [
                "job board",
                "social media",
                "community",
                "publication",
                "aggregator",
            ],
        },
    )  # want to be reading this from model choices directly


@permission_required("products.view_jobtitle")
def titles_annotation(request):
    titles = JobTitle.objects.all()
    return render(
        request, "titles_annotation.html", {"titles": list(titles.values("name"))}
    )


@permission_required("products.change_jobtitle")
def job_title_translation(request):
    return render(request, "titles_translation.html", {})


@permission_required("products.change_jobtitle")
def update_title(request):

    payload = json.loads(request.body)
    title = JobTitle.objects.get(pk=payload["id"])

    update_fields = ["active", "canonical", "name_de", "name_nl"]
    for field in update_fields:
        if field in payload:
            setattr(title, field, payload[field])

    if "alias_of__id" in payload:
        title.alias_of = (
            None
            if payload["alias_of__id"] is None
            else JobTitle.objects.get(pk=payload["alias_of__id"])
        )

    title.save()

    LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(JobTitle).pk,
        object_id=title.id,
        object_repr=title.name,
        action_flag=CHANGE,
    )
    return JsonResponse(
        {
            "active": title.active,
            "canonical": title.canonical,
            "alias_of__id": None if title.alias_of is None else title.alias_of.id,
            "name_de": None if title.name_de is None else title.name_de,
            "name_nl": None if title.name_nl is None else title.name_nl,
        }
    )


def dashboard(request):
    return render(request, "data_quality_dashboard.html")


@permission_required("products.view_product")
def get_boards(request):
    boards = Product.objects.filter().all()

    def build_output():
        output = []
        for board in boards.prefetch_related(
            *["locations", "industries", "job_functions"]
        ).all():
            funs = []
            for fun in board.job_functions.all():
                funs.append(fun.name)

            inds = list(board.industries.values_list("name", flat=True))

            sf_inds = board.salesforce_industries

            locs = []
            for loc in board.locations.all():
                locs.append(
                    {"canonical_name": loc.canonical_name, "mapbox_id": loc.mapbox_id}
                )

            monthly_visits = (
                board.similarweb_estimated_monthly_visits
                if (board.similarweb_estimated_monthly_visits is not None)
                else []
            )

            top_country_shares = (
                board.similarweb_top_country_shares
                if not (board.similarweb_top_country_shares is not None)
                else []
            )

            output.append(
                {
                    "id": board.id,
                    "title": board.title,
                    "description": board.description,
                    "jobfunctions": funs,
                    "industries": inds,
                    "salesforce_industries": sf_inds,
                    "salesforce_product_category": board.salesforce_product_category,
                    "url": board.url,
                    "logo_url": board.logo_url,
                    "channel_type": "missing",
                    "location": locs,
                    "interests": board.interests,
                    "similarweb_estimated_monthly_visits": monthly_visits,
                    "similarweb_top_country_shares": top_country_shares,
                }
            )
        return output

    return JsonResponse({"boards": build_output()}, safe=False)


@permission_required("products.view_product")
def get_products_text_json(request):
    products = Product.objects.order_by("id")
    return JsonResponse(
        {
            "products_text": list(
                products.values("id", "title_en", "description_en", "url")
            )
        }
    )


@permission_required("products.view_product")
def get_product_json(request, id):
    product = Product.objects.get(pk=id)

    funs = []
    for fun in product.job_functions.all():
        funs.append(fun.name)

    inds = list(product.industries.values_list("name", flat=True))

    sf_inds = list(product.salesforce_industries)

    locs = []
    for loc in product.locations.all():
        locs.append(loc.fully_qualified_place_name())

    monthly_visits = (
        product.similarweb_estimated_monthly_visits
        if (product.similarweb_estimated_monthly_visits is not None)
        else []
    )

    top_country_shares = (
        product.similarweb_top_country_shares
        if not (product.similarweb_top_country_shares is not None)
        else []
    )

    return JsonResponse(
        {
            "product": {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "jobfunctions": funs,
                "industries": inds,
                "salesforce_industries": sf_inds,
                "url": product.url,
                "logo_url": product.logo_url,
                "channel_type": "missing",
                "location": locs,
                "interests": product.interests,
                "similarweb_estimated_monthly_visits": monthly_visits,
                "similarweb_top_country_shares": top_country_shares,
            }
        }
    )


@permission_required("products.view_jobtitle")
def get_job_titles_json(request):
    titles = JobTitle.objects.filter()
    return JsonResponse(
        {
            "titles": list(
                titles.values(
                    "id",
                    "name",
                    "job_function__name",
                    "canonical",
                    "alias_of__name",
                    "alias_of__id",
                    "active",
                    "frequency",
                    "name_en",
                    "name_de",
                    "name_nl",
                )
            )
        }
    )


@permission_required("products.view_jobfunction")
def get_job_functions_json(request):
    functions = JobFunction.objects  # .filter(active=True)
    return JsonResponse(
        {"jobFunctions": list(functions.values("name", "parent__name"))}
    )


@permission_required("products.view_location")
def get_locations_json(request):
    locations = Location.objects.all()
    return JsonResponse(
        {
            "locations": list(
                locations.values(
                    "id",
                    "canonical_name",
                    "mapbox_within__canonical_name",
                    "mapbox_id",
                    "mapbox_within__mapbox_id",
                    "approved",
                )
            )
        }
    )


@permission_required("products.view_jobtitle")
def autocomplete(request):
    q = request.GET["q"]
    titles = JobTitle.objects.filter(name__icontains=q).filter().order_by("-freq").all()
    return HttpResponse([name["name"] + "\n" for name in titles.values("name")])


@permission_required("products.change_product")
def add_categorisation(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    board = Product.objects.get(pk=payload["id"])
    field = getattr(board, payload["field"])
    if payload["field"] == "industries":
        industry = Industry.objects.get(name=payload["categoryName"])
        board.industries.add(industry)
        board.save()

    if payload["field"] == "job_functions":
        jobFunction = JobFunction.objects.get(name=payload["categoryName"])
        board.job_functions.add(jobFunction)
        board.save()

    if payload["field"] == "channel_type":
        # simple value rather than a relation
        board.channel_type = payload["categoryName"]
        board.save()

    return JsonResponse(
        {
            "industry": list(board.industries.all().values_list("name", flat=True)),
            "jobFunctions": list(
                board.job_functions.all().values_list("name", flat=True)
            ),
            "channelType": "",
        }
    )


@permission_required("products.change_product")
def set_category_values(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    board = Product.objects.get(pk=payload["id"])
    # field = getattr(board, payload["field"])
    if payload["field"] == "jobfunctions":
        func_names = payload["categoryNames"]
        board.job_functions.clear()
        for func_name in func_names:
            try:
                func = JobFunction.objects.get(name=func_name)
                board.job_functions.add(func)
            except:
                print("Cannot find job function called: " + func_name)

        board.save()

    return JsonResponse(
        {
            "industry": list(board.industries.all().values_list("name", flat=True)),
            "jobFunctions": list(
                board.job_functions.all().values_list("name", flat=True)
            ),
            "channelType": "",
        }
    )


@permission_required("products.change_product")
def set_locations(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    board = Product.objects.get(pk=payload["id"])

    location_names = payload["locations"]
    board.locations.clear()
    for loc_name in location_names:
        try:
            location = Location.objects.get(canonical_name=loc_name)
            board.locations.add(location)
        except:
            print("cannot find a location called: " + loc_name)

    board.save()
    return JsonResponse(
        {
            "industry": list(board.industries.all().values_list("name", flat=True)),
            "jobFunctions": list(
                board.job_functions.all().values_list("name", flat=True)
            ),
            "channelType": "",
            "locations": list(
                board.locations.all().values_list("canonical_name", flat=True)
            ),
        }
    )


def export_options_json(request):
    return JsonResponse(
        {
            "categories": list(
                Industry.objects.all().values("name_en", "name_de", "name_nl")
            ),
            "job_functions": list(
                JobFunction.objects.all().values("name", "parent__name")
            ),
        }
    )


def export_categories_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="categories.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name EN", "Name DE", "Name NL"])
    for category in Industry.objects.all():
        writer.writerow([category.name_en, category.name_de, category.name_nl])

    return response
