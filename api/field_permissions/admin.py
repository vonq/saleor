class PermissionBasedFieldsMixin:
    """
    A mixin for AdminModel
    to enable hiding field or setting fields as read-only
    according to the permission of "can_(view|change)_model_field".
    """

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        unavailable_fields = tuple(
            field
            for field in self.fields
            if not self.model.has_field_change_perm(request.user, field)
        )

        return tuple(readonly_fields) + unavailable_fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [
            field
            for field in fields
            if any(
                (
                    self.model.has_field_view_perm(request.user, field),
                    self.model.has_field_change_perm(request.user, field),
                )
            )
        ]
