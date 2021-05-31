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



class Tracking(serializers.Serializer):
    vacancyUrl = serializers.URLField(allow_null=False)
    applicationUrl = serializers.URLField(allow_null=False)
    utm = serializers.CharField(allow_null=False)



class Taxonomy(serializers.Serializer):
    industry = serializers.IntegerField(allow_null=False)
    jobCategory = serializers.IntegerField(allow_null=False)
    seniority = serializers.IntegerField(allow_null=False)
    tracking = serializers.IntegerField(allow_null=False)



class VacancyDetails(serializers.Serializer):
    jobTitle = serializers.CharField(max_length=255, allow_null=False)
    description = serializers.CharField(allow_null=False)
    companyLogo = serializers.URLField(allow_null=False)
    taxonomy = Taxonomy(allow_null=False)



class ContactInfo(serializers.Serializer):
    phoneNumber = serializers.CharField(allow_null=False)



class CheckoutMetadata(serializers.Serializer):
    vacancy = VacancyDetails(allow_null=False)
    contactInfo = ContactInfo(allow_null=False)
