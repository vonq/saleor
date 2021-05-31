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
    industryId = serializers.IntegerField(allow_null=False)
    jobCategoryId = serializers.IntegerField(allow_null=False)
    seniorityId = serializers.IntegerField(allow_null=False)
    seniorityId = serializers.IntegerField(allow_null=False)
    educationLevelId = serializers.IntegerField(allow_null=False)

class WorkingHours(serializers.Serializer):
    minimum = serializers.IntegerField(min_value=1, allow_null=False)
    maximum = serializers.IntegerField(min_value=1, allow_null=False)

    def validate(self, attrs):
        if attrs["maximum"] < attrs["minimum"]:
            raise serializers.ValidationError("Maximum working hours needs to be greater than or equal to minimum working hours")
        return attrs


class Salary(serializers.Serializer):
    minimumAmount = serializers.IntegerField(min_value=1, allow_null=False)
    maximumAmount = serializers.IntegerField(min_value=1, allow_null=False)
    perPeriod = serializers.ChoiceField(choices=["yearly", "monthly", "weekly", "daily", "hourly"])

    def validate(self, attrs):
        if attrs["maximumAmount"] < attrs["minimumAmount"]:
            raise serializers.ValidationError("Maximum salary amount needs to be greater than or equal to minimum salary amount")
        return attrs


class VacancyDetails(serializers.Serializer):
    jobTitle = serializers.CharField(max_length=255, allow_null=False)
    organizationName = serializers.CharField(max_length=255, allow_null=False)
    type = serializers.ChoiceField(choices=["permanent", "temporary", "fixed_term", "fixed_term_with_option_for_permanent", "freelance", "traineeship", "internship"], allow_null=False)
    description = serializers.CharField(allow_null=False)
    companyLogo = serializers.URLField(allow_null=False)
    taxonomy = Taxonomy(allow_null=False)
    workingHours = WorkingHours(allow_null=False)
    salary = Salary(allow_null=False)



class ContactInfo(serializers.Serializer):
    name = serializers.CharField(allow_null=False)
    phoneNumber = serializers.CharField(allow_null=False)
    emailAddress = serializers.EmailField(allow_null=False)



class CheckoutMetadata(serializers.Serializer):
    vacancy = VacancyDetails(allow_null=False)
    contactInfo = ContactInfo(allow_null=False)
