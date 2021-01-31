from django.shortcuts import get_object_or_404


class MultipleRequiredFieldLookupMixin:
    """
    Apply this mixin to any detail view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute and an optional `lookup_url_kwargs`
    attribute, instead of the default single field filtering.
    """

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwargs = self.lookup_fields

        if hasattr(self, "lookup_url_kwargs") and self.lookup_url_kwargs is not None:
            lookup_url_kwargs = self.lookup_url_kwargs

            assert len(self.lookup_url_kwargs) == len(
                self.lookup_fields
            ), "`.lookup_fields` and `.lookup_url_kwargs` attributes must be of equal length"

        for lookup_url_kwarg in lookup_url_kwargs:
            assert lookup_url_kwarg in self.kwargs, (
                f"Expected view {self.__class__.__name__} to be called with a URL keyword argument "
                f"named '{lookup_url_kwarg}'. Fix your URL conf, or set the `.lookup_fields|.lookup_url_kwargs` "
                f"attribute on the view correctly."
            )

        filter_kwargs = {
            lookup_field: self.kwargs[lookup_field_kwarg]
            for lookup_field, lookup_field_kwarg in zip(self.lookup_fields, lookup_url_kwargs)
        }

        obj = get_object_or_404(queryset, **filter_kwargs)  # Lookup the object

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
