class FieldPermissionModelMixin:
    VIEW_FIELD_PERMISSION_TEMPLATE = "can_view_{model_name}_{field_name}"
    CHANGE_FIELD_PERMISSION_TEMPLATE = "can_change_{model_name}_{field_name}"

    class Meta:
        abstract = True

    def _has_perm(self, user, label):
        if label not in dict(self._meta.permissions):
            return True
        return user.has_perm(f"{self._meta.app_label}.{label}")

    def has_field_view_perm(self, user, field):
        return self._has_perm(
            user,
            self.VIEW_FIELD_PERMISSION_TEMPLATE.format(
                model_name=self._meta.model_name, field_name=field
            ),
        )

    def has_field_change_perm(self, user, field):
        return self._has_perm(
            user,
            self.CHANGE_FIELD_PERMISSION_TEMPLATE.format(
                model_name=self._meta.model_name, field_name=field
            ),
        )
