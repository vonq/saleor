from modeltranslation.translator import register, TranslationOptions
from api.vonqtaxonomy.models import (
    Industry,
    JobCategory,
)


@register(Industry)
class IndustryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(JobCategory)
class JobCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)
