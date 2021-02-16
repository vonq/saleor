from rest_framework.pagination import LimitOffsetPagination

from api.products.search.index import ProductIndex


class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 25
    max_limit = 100


class AutocompleteResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 20


class SearchResultsPagination(StandardResultsSetPagination):
    MAX_RETRIEVABLE_RESULTS = ProductIndex.settings["paginationLimitedTo"]

    def paginate_queryset(self, queryset, request, view=None):
        self.count = min(view.search_results_count, self.MAX_RETRIEVABLE_RESULTS)

        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []

        return queryset
