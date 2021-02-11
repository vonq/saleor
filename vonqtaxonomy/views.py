from django.db.models import Q

from django.http import JsonResponse
from rest_framework.decorators import permission_classes

import api.vonqtaxonomy
from api.products.views import IsMapiUser
from api.vonqtaxonomy.models import Industry, JobCategory


@permission_classes((IsMapiUser,))
def get_job_category_mapping(request):
    text = request.GET.get("job_function_name")
    if not text:
        return JsonResponse({"error": "No job function name specified"}, status=400)

    try:
        job_category = JobCategory.objects.get(
            Q(jobfunction__name_en__iexact=text)
            | Q(jobfunction__name_nl__iexact=text)
            | Q(jobfunction__name_de__iexact=text)
        )
    except api.vonqtaxonomy.models.JobCategory.DoesNotExist:
        return JsonResponse({"error": "Mapping not found"}, status=404)

    return JsonResponse(
        {
            "name": job_category.name_nl,  # Items from VONQ taxonomy in IGB are all in Dutch,,
            "id": job_category.mapi_id,
        }
    )


@permission_classes((IsMapiUser,))
def get_industry_mapping(request):
    text = request.GET.get("industry_name")
    if not text:
        return JsonResponse({"error": "No industry name specified"}, status=400)
    try:
        industry = Industry.objects.get(
            Q(industry__name_en__iexact=text)
            | Q(industry__name_nl__iexact=text)
            | Q(industry__name_de__iexact=text)
        )
    except api.vonqtaxonomy.models.Industry.DoesNotExist:
        return JsonResponse({"error": "Mapping not found"}, status=404)

    return JsonResponse(
        {
            "name": industry.name_nl,  # Items from VONQ taxonomy in IGB are all in Dutch,
            "id": industry.mapi_id,
        }
    )
