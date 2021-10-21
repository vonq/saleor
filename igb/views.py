from django.http import JsonResponse
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from api.igb.apps import IgbConfig
from api.igb.models import Contract
from api.igb.serializers import (
    ContractSerializer,
    DecryptedContractSerializer,
    ValidateContractSerializer,
)
from api.products.docs import CommonOpenApiParameters
from api.products.models import Product
from api.products.paginators import StandardResultsSetPagination
from api.products.views import IsInternalUser, IsExternalATSUserWithMOC


class ContractViewSet(
    GenericViewSet, CreateModelMixin, RetrieveModelMixin, ListModelMixin
):
    model = Contract
    serializer_class = ContractSerializer
    permission_classes = [IsInternalUser | IsExternalATSUserWithMOC]
    queryset = Contract.objects.all()
    pagination_class = StandardResultsSetPagination
    lookup_field = "contract_id"

    def get_queryset(self):
        # TODO: abstract this out in a middleware
        customer_id = self.request.headers.get("X-Customer-Id")
        return Contract.objects.filter(customer_id=customer_id)

    @swagger_auto_schema(
        operation_description="""
                This endpoint creates a new customer contract.
                It requires a reference to a channel, a credential payload,
                and the facets set for the my own contracted product.
            """,
        operation_id="Create a new customer contract",
        operation_summary="Create a new customer contract",
        tags=[IgbConfig.verbose_name],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
            This endpoint retrieves the detail for a customer contract.
            It contains a reference to a channel, an (encrypted) credential payload,
            and the facets set for the my own contracted product.
        """,
        operation_id="Details for a customer contract",
        operation_summary="Details for a customer contract",
        tags=[IgbConfig.verbose_name],
        manual_parameters=[CommonOpenApiParameters.CUSTOMER_ID],
        responses={200: DecryptedContractSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DecryptedContractSerializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="""
            This endpont exposes a list of multiple contracts, if available to a specific user.
        """,
        operation_id="Multiple details of customer contracts",
        operation_summary="Multiple details of customer contracts",
        tags=[IgbConfig.verbose_name],
        manual_parameters=[CommonOpenApiParameters.CUSTOMER_ID],
        responses={200: DecryptedContractSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="multiple/(?P<contract_ids>.+)",
    )
    def multiple(self, request, contract_ids=None):
        if not contract_ids:
            raise NotFound

        contract_ids = contract_ids.split(",")
        if len(contract_ids) > 50:
            return JsonResponse(
                data={"error": "Cannot fetch more than 50 contracts at a time"},
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.get_queryset().filter(contract_id__in=contract_ids)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = DecryptedContractSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DecryptedContractSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="""
            This endpoint exposes a list of contract available to a particular user.
        """,
        operation_id="List contracts available for a customer",
        operation_summary="List contract available for a customer",
        tags=[IgbConfig.verbose_name],
        manual_parameters=[CommonOpenApiParameters.CUSTOMER_ID],
        responses={200: DecryptedContractSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
                This endpoint allows the validation of a list of {contractId, productId} objects.
                It will return a validation response.
            """,
        operation_id="Validate customer MoC order",
        operation_summary="Validate customer MoC order",
        request_body=ValidateContractSerializer(many=True),
        responses={
            400: openapi.Response(
                "failure",
            ),
            200: serializer_class("success", many=True),
        },
        tags=[IgbConfig.verbose_name],
        manual_parameters=[CommonOpenApiParameters.CUSTOMER_ID],
    )
    @action(
        methods=["post"],
        detail=False,
        url_path="validate",
    )
    def validate(self, request):
        serialized_data = ValidateContractSerializer(data=request.data, many=True)

        serialized_data.is_valid(raise_exception=True)

        errors = {}

        for contract in serialized_data.data:
            contract_id = contract["contract_id"]
            product_id = contract["product_id"]

            product = Product.objects.filter(product_id=product_id, moc_only=True)
            if not product:
                errors[product_id] = f"Invalid MyContract product: {product_id}"
                continue

            contract = Contract.objects.filter(
                contract_id=contract_id,
                channel=product[0].channel,
                customer_id=request.headers.get("X-Customer-Id"),
            )

            if not contract:
                errors[product_id] = f"Invalid contract: {contract_id}"

        if errors:
            return JsonResponse(data=errors, status=400)

        return Response(serialized_data.data, status=200)
