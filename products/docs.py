from drf_yasg2 import openapi


class CommonParameters:
    ACCEPT_LANGUAGE = openapi.Parameter(
        name="Accept-Language",
        enum=["en", "nl", "de"],
        in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        format="language tag",
        required=False,
        description="The language the client prefers.",
    )
    PRODUCT_NAME = (
        openapi.Parameter(
            "name",
            in_=openapi.IN_QUERY,
            description="Search text for a product name",
            type=openapi.TYPE_STRING,
            required=False,
            example="Monster.com",
        ),
    )
