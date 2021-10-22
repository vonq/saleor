from enum import Enum
from typing import Union, Iterable

from saleor.core.permissions import BasePermissionEnum
from saleor.graphql.decorators import account_passes_test


class CheckoutPermissions(BasePermissionEnum):
    WRITE_CHECKOUTS = "write:checkouts"
    READ_CHECKOUTS = "read:checkouts"


def _permission_required(perms: Iterable[Enum], context):
    if context.remote_user and set(map(lambda x: x.value, perms)) <= set(
            context.remote_user.permissions):
        return True
    return False


def remote_permission_required(perm: Union[Enum, Iterable[Enum]]):
    def check_perms(context):
        if isinstance(perm, Enum):
            perms = (perm,)
        else:
            perms = perm
        return _permission_required(perms, context)

    return account_passes_test(check_perms)
