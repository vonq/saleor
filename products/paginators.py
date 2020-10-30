from rest_framework.pagination import LimitOffsetPagination


class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 100


class AutocompleteResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 20
