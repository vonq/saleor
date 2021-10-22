import ast
from django_better_admin_arrayfield.models.fields import DynamicArrayField
from django.contrib.postgres.fields import ArrayField as DjangoArrayField


class PKBDynamicArrayField(DynamicArrayField):
    """
    A fixed version of DynamicArrayField
    required until https://github.com/gradam/django-better-admin-arrayfield/issues/174
    gets fixed upstream.
    """

    def _coerce(self, data):
        if isinstance(data, str):
            return ast.literal_eval(data)
        return self.to_python(data)


class PKBArrayField(DjangoArrayField):
    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": PKBDynamicArrayField, **kwargs})
