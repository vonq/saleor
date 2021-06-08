from drf_yasg2 import openapi


class CommonOpenApiParameters:
    ACCEPT_LANGUAGE = openapi.Parameter(
        name="Accept-Language",
        enum=["en", "nl", "de"],
        in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        format="language tag",
        required=False,
        description="The language the client prefers.",
    )
    CURRENCY = openapi.Parameter(
        "currency",
        in_=openapi.IN_QUERY,
        description="ISO-4217 code for a currency.",
        type=openapi.TYPE_STRING,
        required=False,
        example="GBP",
    )
