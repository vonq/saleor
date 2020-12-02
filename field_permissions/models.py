class FieldPermissionModelMixin:
    VIEW_FIELD_PERMISSION_TEMPLATE = "can_view_{model_name}_{field_name}"
    CHANGE_FIELD_PERMISSION_TEMPLATE = "can_change_{model_name}_{field_name}"

    class Meta:
        abstract = True

    @classmethod
    def _has_perm(cls, user, label):
        if label not in dict(cls._meta.permissions):
            return True
        return user.has_perm(f"{cls._meta.app_label}.{label}")

    @classmethod
    def has_field_view_perm(cls, user, field):
        return cls._has_perm(
            user,
            cls.VIEW_FIELD_PERMISSION_TEMPLATE.format(
                model_name=cls._meta.model_name, field_name=field
            ),
        )

    @classmethod
    def has_field_change_perm(cls, user, field):
        return cls._has_perm(
            user,
            cls.CHANGE_FIELD_PERMISSION_TEMPLATE.format(
                model_name=cls._meta.model_name, field_name=field
            ),
        )
