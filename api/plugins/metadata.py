from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField


"""
{
  "vacancy.jobTitle": "string, not null, max 255 characters",
  "vacancy.description":  "string, max 10,000 characters, plain text or valid html",
  "vacancy.companyLogo": "valid url, existent jpg or png file",
  "vacancy.taxonomy.industry": "valid pkb id",
  "vacancy.taxonomy.jobCategoryId": "valid pkb id",
  "vacancy.taxonomy.seniority": "valid id. hardcoded ids from mapi for now. to-do: import taxonomy to pkb",
  "vacancy.tracking.vacancyUrl": "valid http url returning 2xx status code",
  "vacancy.tracking.applicationUrl": "valid http url returning 2xx status code",
  "vacancy.tracking.utm": "array of objects {productId: valid pkb id, utm: valid query params string}",
  "contactInfo.name": "string, max 64 characters",
  "contactInfo.phoneNumber": "string, valid international phone number",
}
"""

class MetadataSerializer(serializers.Serializer):
    vacancy_jobTitle = serializers.CharField(max_length=255, allow_null=True, required=False)
    vacancy_description = serializers.CharField(max_length=10000, allow_null=True, required=False)
    vacancy_companyLogo = serializers.URLField(allow_null=True, required=False)
    vacancy_taxonomy_industry = serializers.IntegerField(allow_null=True, required=False)
    vacancy_taxonomy_jobCategoryId = serializers.IntegerField(allow_null=True, required=False)
    vacancy_taxonomy_seniority = serializers.IntegerField(allow_null=True, required=False)
    vacancy_tracking_vacancy_url = serializers.URLField(allow_null=True, required=False)
    vacancy_tracking_applicationUrl = serializers.URLField(allow_null=True, required=False)
    vacancy_tracking_utm = serializers.ListSerializer(child=serializers.CharField(), allow_empty=True, allow_null=True, required=False)
    contactInfo_name = serializers.CharField(max_length=64, allow_null=True, required=False)
    contactInfo_phoneNumber = PhoneNumberField(allow_null=True, required=False)



class FinalMetadataSerializer(MetadataSerializer):
    vacancy_jobTitle = serializers.CharField(max_length=255, allow_null=False, required=True)
    vacancy_description = serializers.CharField(max_length=10000, allow_null=False, required=True)
    vacancy_companyLogo = serializers.URLField(allow_null=False, required=True)
    vacancy_taxonomy_industry = serializers.IntegerField(allow_null=False, required=True)
    vacancy_taxonomy_jobCategoryId = serializers.IntegerField(allow_null=False, required=True)
    vacancy_taxonomy_seniority = serializers.IntegerField(allow_null=False, required=True)
    vacancy_tracking_vacancy_url = serializers.URLField(allow_null=False, required=True)
    vacancy_tracking_applicationUrl = serializers.URLField(allow_null=False, required=True)
    vacancy_tracking_utm = serializers.ListSerializer(child=serializers.CharField(), allow_empty=False, allow_null=True, required=True)
    contactInfo_name = serializers.CharField(max_length=64, allow_null=False, required=True)
    contactInfo_phoneNumber = PhoneNumberField(allow_null=False, required=True)
