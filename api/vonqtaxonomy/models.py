from django.db import models


class JobCategory(models.Model):
    mapi_id = models.IntegerField()
    name = models.CharField(max_length=255)

    @property
    def get_nl_name(self):
        return self.name_nl

    def __str__(self):
        return self.name


class Industry(models.Model):
    mapi_id = models.IntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
