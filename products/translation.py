from modeltranslation.translator import register, TranslationOptions
from api.products.models import (
    Industry,
    JobFunction,
    JobTitle,
    Location,
    Channel,
    Product,
)


@register(Industry)
class IndustryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(JobFunction)
class JobFunctionTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(JobTitle)
class JobTitleTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ("canonical_name",)


@register(Channel)
class ChannelTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("title", "description")
