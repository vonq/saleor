from drf_yasg2 import openapi


class ProductsOpenApiParameters:
    PRODUCT_NAME = openapi.Parameter(
        "name",
        in_=openapi.IN_QUERY,
        description="Search text for a product name.",
        type=openapi.TYPE_STRING,
        required=False,
        example="Monster.com",
    )
    ONLY_RECOMMENDED = openapi.Parameter(
        "recommended",
        in_=openapi.IN_QUERY,
        description="Only return recommended products.",
        type=openapi.TYPE_BOOLEAN,
        default=False,
        required=False,
    )
    SORT_BY = openapi.Parameter(
        "sortBy",
        in_=openapi.IN_QUERY,
        description="Sort products by different criteria.",
        type=openapi.TYPE_STRING,
        enum=["relevant", "recent"],
        default="relevant",
        required=False,
        example="recent",
    )
