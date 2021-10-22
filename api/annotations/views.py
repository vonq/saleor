from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import permission_required, login_required

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_http_methods

from api.annotations import TITLE_FUNC_MAPPINGS
from api.products.serializers import MinimalProductSerializer

from api.products.models import (
    Industry,
    Product,
    JobFunction,
    JobTitle,
    Location,
    Channel,
    Category,
    PostingRequirement,
)

from api import settings

import json
import csv
import os
import requests
import urllib

from django.db.models import Q


def index(request):
    return render(request, "index.html")


def product_annotation(request):
    industries = Industry.objects.all()
    categories = Category.objects.all()
    jobFunctions = JobFunction.objects.all()
    return render(
        request,
        "product_annotation.html",
        {
            "industries": list(industries.values("name")),
            "categories": list(categories.values("name")),
            "jobFunctions": list(jobFunctions.values("name")),
            "channelTypes": [choice[0] for choice in Channel.Type.choices],
        },
    )


@permission_required("products.view_channel")
def channel_annotation(request):
    return render(
        request,
        "channel_annotation.html",
        {"type_options": [choice[0] for choice in Channel.Type.choices]},
    )


@permission_required("products.view_channel")
def get_channel_list_json(request):
    channels = Channel.objects.distinct()

    return JsonResponse(
        {
            "channels": list(
                channels.values("id", "url", "name_en", "name_de", "name_nl", "type")
            )
        }
    )


@permission_required("products.view_channel")
def get_channel_json(request, channel_id):
    # include a request to get title from URL?
    channel = Channel.objects.filter(pk=channel_id)
    print(channel.values("product__description"))
    return JsonResponse(
        {
            "type": channel.first().type,
            "products": list(
                channel.values_list(
                    "product__title", "product__description", "product__url"
                )
            ),
        }
    )


@permission_required("products.change_channel")
def update_channel(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    channel = Channel.objects.get(pk=payload["id"])

    channel.type = payload["type"]
    channel.save()

    return JsonResponse({"type": channel.type})


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


def search_relevancy(request):
    return render(request, "search_relevancy_dashboard.html")


@permission_required("products.change_product")
def posting_requirements(request):
    return render(request, "posting_requirements.html")


@permission_required("products.change_product")
def set_posting_requirements(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse(
            {"status": "error", "message": "Request body cannot be parsed as a JSON"}
        )

    try:
        product = Product.objects.get(salesforce_id=payload["uuid"])
    except ObjectDoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "No product with uuid " + payload["uuid"]}
        )

    values = payload["values"].split(",")
    product.posting_requirements.clear()
    for value in values:
        posting_requirement, created = PostingRequirement.objects.get_or_create(
            posting_requirement_type=value
        )
        product.posting_requirements.add(posting_requirement)

    return JsonResponse(
        {"status": "ok", "message": "Updated product #" + str(product.id)}
    )


@permission_required("products.view_product")
def get_products(request):
    products = Product.objects.filter().all()

    def build_output():
        output = []
        for product in products.prefetch_related(
            *["locations", "industries", "job_functions"]
        ).all():
            funs = []
            for fun in product.job_functions.all():
                funs.append(fun.name)

            inds = list(product.industries.values_list("name", flat=True))

            sf_inds = product.salesforce_industries

            locs = []
            for loc in product.locations.all():
                locs.append(
                    {"canonical_name": loc.canonical_name, "mapbox_id": loc.mapbox_id}
                )

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

            output.append(
                {
                    "id": product.id,
                    "title": product.title,
                    "status": product.status,
                    "is_active": product.is_active,
                    "is_recommended": product.is_recommended,
                    "description": product.description,
                    "jobfunctions": funs,
                    "industries": inds,
                    "salesforce_industries": sf_inds,
                    "salesforce_product_category": product.salesforce_product_category,
                    "url": product.url,
                    "logo_url": product.logo_url,
                    "location": locs,
                    "interests": product.interests,
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
        locs.append(loc.fully_qualified_place_name)

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
                    "mapbox_context",
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


def find_parent(node_value, relations):
    for relation in relations:
        if node_value == relation["child"]:
            return relation["parent"]  # single parent
    return None


def find_children(node_value, relations):
    children = []  # multiple children
    for relation in relations:
        if node_value == relation["parent"]:
            children.append(relation["child"])
    return children


def expand_to_branch(nodes, relations):
    def find_ancestors(node_value):  # returns a list from a value
        parent = find_parent(node_value, relations)
        if parent is None:
            return []
        else:
            ancestors = find_ancestors(parent)
            ancestors.append(parent)
            return ancestors

    branch = []
    for node in nodes:
        branch.append(node)
        branch.extend(find_ancestors(node))
        branch.extend(find_descendents(node, relations))
    return list(set(branch))  # to unique values


def find_descendents(node_value, relations):  # returns a list from a value
    children = find_children(node_value, relations)
    descendents = []
    for child in children:
        descendents.append(child)
        descendents.extend(find_descendents(child, relations))
    return descendents
    # return ancestors and descendants of given items


def depth_on_branch(node, relations):
    parent = find_parent(node, relations)
    if parent is None:
        return 0
    else:
        return 1 + depth_on_branch(parent, relations)


@permission_required("products.view_product")
def reference_product_search(request):
    query_job_function_ids = list(
        map(lambda x: int(x), request.GET["job_function_ids"].split(","))
    )
    query_location_ids = list(
        map(lambda x: int(x), request.GET["location_ids"].split(","))
    )

    all_approved_locations = Location.objects.filter(approved=True)

    location_relations = [
        {"parent": loc["mapbox_within__id"], "child": loc["id"]}
        for loc in list(
            all_approved_locations.values(
                "id", "canonical_name_en", "mapbox_within__id"
            )
        )
        if loc["mapbox_within__id"] is not None
    ]
    expanded_locations = expand_to_branch(query_location_ids, location_relations)

    all_functions = JobFunction.objects.all()
    function_relations = [
        {
            "parent": loc["parent__id"],
            "child": loc["id"],
            "label": loc["name_en"] + " > " + loc["parent__name_en"],
        }
        for loc in list(
            all_functions.values("id", "name_en", "parent__id", "parent__name_en")
        )
        if loc["parent__id"] is not None
    ]

    expanded_functions = expand_to_branch(query_job_function_ids, function_relations)

    products = Product.objects.filter(
        Q(job_functions__id__in=expanded_functions)
        & Q(locations__id__in=expanded_locations)
        & Q(status=Product.Status.ACTIVE)
    )

    # need to find depth of most specific location matching the search query
    location_specificity_lookup = {}
    for product in products.all():
        max_location_depth = -1
        for location in product.locations.all():
            location_depth = depth_on_branch(location.id, location_relations)
            if location.id in query_location_ids:
                max_location_depth = max(max_location_depth, location_depth)
            else:
                for query_location_id in query_location_ids:
                    # match up from children
                    if location.id in find_descendents(
                        query_location_id, location_relations
                    ):
                        # limit depth to query level. Currently producing -1 for International
                        max_location_depth = max(
                            max_location_depth,
                            depth_on_branch(query_location_id, location_relations),
                        )
        location_specificity_lookup[product.id] = max_location_depth

    queryset = products.all()

    for product in queryset:
        product.location_specificity = location_specificity_lookup[product.id]

    serializer = MinimalProductSerializer(queryset, many=True)
    return JsonResponse(serializer.data, safe=False)


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
def migrate_industry_to_category(request):
    try:
        payload = json.loads(request.body)
    except (TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    products = Product.objects.filter(industries__name_en=payload["industry_name"])
    category, created = Category.objects.get_or_create(name_en=payload["industry_name"])

    for product in products:
        product.categories.add(category)
        product.save()

    return JsonResponse(
        {"status": "OK", "message": "migrated " + str(products.count()) + " categories"}
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


@permission_required("products.change_channel")
def set_channel(request):
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    channel = Channel.objects.get(pk=payload["id"])

    if payload["type"] is not None and payload["type"] in [
        choice[0] for choice in Channel.Type.choices
    ]:
        channel.type = payload["type"]
        channel.save()

    return JsonResponse({"type": channel.type})


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


def parse_title_testbench(request):
    return render(request, "parse_title_testbench.html")


def parse_headline_checker(request):
    return render(request, "headline-parser.html")


def parse_title(request):
    exclusion_list = ["&", "/", "senior", "specialist", "expert"]
    try:
        payload = json.loads(request.body)
    except TypeError:
        return JsonResponse({"error": "Request body cannot be parsed as a JSON"})

    if payload["title"] is None:
        return JsonResponse({"status": "error"})

    title = payload["title"]

    freqs = {"funcs": {}, "tokens": {}}
    for d in TITLE_FUNC_MAPPINGS:
        if d["func"] not in freqs["funcs"]:
            freqs["funcs"][d["func"]] = {}
        tokens = d["title"].lower().split(" ")
        for t in tokens:
            if t in exclusion_list:
                continue
            if t in freqs["funcs"][d["func"]]:
                freqs["funcs"][d["func"]][t] = freqs["funcs"][d["func"]][t] + 1
            else:
                freqs["funcs"][d["func"]][t] = 1
            if t in freqs["tokens"]:
                freqs["tokens"][t] = freqs["tokens"][t] + 1
            else:
                freqs["tokens"][t] = 1  # marginals

    freqs["funcs"][None] = {}
    freqs["tokens"][None] = {}

    def tokenise(text):
        return text.lower().split(" ")

    for mapping in TITLE_FUNC_MAPPINGS:
        mapping["token_list"] = tokenise(mapping["title"])

    title_func_lookup = {m["title"].lower(): m["func"] for m in TITLE_FUNC_MAPPINGS}

    def get_job_functions(title_text):
        title_text = title_text.lower()
        # look for exact match
        if title_text in title_func_lookup:
            return {
                "functions": [{"function": title_func_lookup[title_text]}],
                "estimation_type": "exact_match",
            }

        # look for sublist of tokens
        sublist_matches = list(filter(sublist_match, TITLE_FUNC_MAPPINGS))

        if len(sublist_matches) > 1:
            sublist_matches.sort(key=lambda x: -len(x))  # larger matches first
            return {"functions": sublist_matches, "estimation_type": "sublist_match"}

        # look for any tokens weight and summed
        return func_dist(title_text)

    def sublist_match(mapping):
        return "token_list" in mapping and contains(
            mapping["token_list"], tokenise(title)
        )

    def contains(subseq, inseq):
        return any(
            inseq[pos : pos + len(subseq)] == subseq
            for pos in range(0, len(inseq) - len(subseq) + 1)
        )

    def func_dist(title_text):
        title_tokens = (
            title_text.lower().strip().split(" ")
        )  # .map(lambda t: t.strip())
        sum_list = []
        for func in freqs["funcs"]:
            sum = 0
            for token in title_tokens:
                if token in freqs["funcs"][func]:
                    sum += freqs["funcs"][func][token] / freqs["tokens"][token]

            if sum > 0 and func != "null":
                sum_list.append({"function": func, "weight": sum})

        sum_list.sort(key=lambda x: -x["weight"])
        return {"functions": sum_list, "estimation_type": "frequency"}

    headers = {
        "X-Algolia-API-Key": settings.ALGOLIA["API_KEY"],
        "X-Algolia-Application-Id": settings.ALGOLIA["APPLICATION_ID"],
        "X-Algolia-UserToken": "testbench",
    }
    r = requests.post(
        "https://OWF766BMHV-dsn.algolia.net/1/indexes/prod_JobFunction/query",
        '{ "params": "query='
        + urllib.parse.quote(title)
        + '&hitsPerPage=2&getRankingInfo=1" }',
        headers=headers,
    )

    return JsonResponse(
        {
            "title": title,
            "title_tokens": tokenise(title),
            "result": get_job_functions(title),
            "algolia": r.json(),
        }
    )
