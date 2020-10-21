from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 100
    
