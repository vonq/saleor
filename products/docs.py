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
