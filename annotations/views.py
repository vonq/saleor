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

@permission_required("annotations.view_product")
def job_title_translation(request):
    return render(
        request, "titles_translation.html", {}
    )

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
            "name_nl": None if title.name_nl is None else title.name_nl
        }
    )


def dashboard(request):
    return render(request, "dashboard.html")


def update_boards(request):
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
                locs.append(loc.fully_qualified_place_name)

            monthlyVisits = (
                json.loads(board.similarweb_estimated_monthly_visits.replace("'", '"'))
                if not (
                    board.similarweb_estimated_monthly_visits is None
                    or board.similarweb_estimated_monthly_visits == ""
                )
                else []
            )

            topCountryShares = (
                json.loads(board.similarweb_top_country_shares.replace("'", '"'))
                if not (
                    board.similarweb_top_country_shares is None
                    or board.similarweb_top_country_shares == ""
                )
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
                    "url": board.url,
                    "logo_url": board.logo_url,
                    "channel_type": "missing",  # board.channel.objects.first().type,
                    "location": locs,
                    "interests": board.interests,
                    "similarweb_estimated_monthly_visits": monthlyVisits,  # ) if not board.similarweb_estimated_monthly_visits is None else {},
                    "similarweb_top_country_shares": topCountryShares,
                }
            )
        return output

    return JsonResponse({"boards": build_output()}, safe=False)


def get_job_titles_json(request):
    titles = JobTitle.objects.filter()
    return JsonResponse(
        {
            "titles": list(
                titles.values(
                    "id",
                    "name",
                    "job_function__name",
                    "industry__name",
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


def get_job_functions_json(request):
    functions = JobFunction.objects  # .filter(active=True)
    return JsonResponse(
        {"jobFunctions": list(functions.values("name", "parent__name"))}
    )


def get_locations_json(request):
    locations = Location.objects.filter()
    return JsonResponse({"locations": list(locations.values("name", "within__name"))})


def autocomplete(request):
    q = request.GET["q"]
    titles = JobTitle.objects.filter(name__icontains=q).filter().order_by("-freq").all()
    return HttpResponse([name["name"] + "\n" for name in titles.values("name")])


@user_passes_test(lambda u: u.is_superuser)
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
