from modeltranslation.translator import register, TranslationOptions
from api.products.models import (
    Industry,
    JobFunction,
    JobTitle,
    Location,
    Channel,
    Product,
    Category,
    PostingRequirement,
)


@register(Industry)
class IndustryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(JobFunction)
class JobFunctionTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(JobTitle)
class JobTitleTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ("canonical_name", "mapbox_text", "mapbox_placename")


@register(Channel)
class ChannelTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(PostingRequirement)
class PostingRequirementOptions(TranslationOptions):
    fields = ("posting_requirement_type",)
