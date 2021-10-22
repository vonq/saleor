from drf_yasg2 import openapi

from api.products.search.index import ProductIndex


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
        description="Only return recommended products. Cannot be used in combination with 'excludeRecommended'",
        type=openapi.TYPE_BOOLEAN,
        default=False,
        required=False,
    )
    EXCLUDE_RECOMMENDED = openapi.Parameter(
        "excludeRecommended",
        in_=openapi.IN_QUERY,
        description=f"Exclude recommended products from search results. Cannot be used in combination with 'recommended'.",
        type=openapi.TYPE_BOOLEAN,
        default=False,
        required=False,
    )
    SORT_BY = openapi.Parameter(
        "sortBy",
        in_=openapi.IN_QUERY,
        description="Sort products by different criteria.",
        type=openapi.TYPE_STRING,
        enum=[
            "relevant",
            "recent",  # needed for HAPI backwards compatibility
        ]
        + list(ProductIndex.SORTING_REPLICAS.keys()),
        default="relevant",
        required=False,
        example="recent",
    )
