from django.shortcuts import get_object_or_404
from django.db.models.query import QuerySet


class MultipleRequiredFieldLookupMixin:
    """
    Apply this mixin to any detail view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute instead of the default single field filtering.

    lookup_fields: dict of the fields that will actually be filtered against on the queryset:

    ## `lookup_fields` Format
    ```python
    {
        # kwargs that was passed in from params mapped to actual kwargs/fields that will be used to filter the
        # queryset against, i.e:
        "username" : "user__username",
        # Or
        "username" : {"filter_kwarg": "user__username", "pk": False},
        # Or if the kwarg(s) will specifically be used as pk value(s) then they can be written as the following:
        "order_number": { "filter_kwarg": "order__no", "pk": True },
        "shipment_number": { "filter_kwarg": "shipment_no", "pk": True },

    }
    ```
    Note: `lookup_fields` will all be required by default except if marked as `"pk": True`, in which case they will
    only be used when calling `get_object()`

    ---

    ## Full example:
    ```python
    # url in the format:  /courses/{owner}/{course_name}
    class CourseDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
        queryset = Course._default_manager.all()
        lookup_fields = {
            "owner": "course__owner__username",
            "course_name": {
                "filter_kwarg": "name",
                "pk": True
            }
        }
    ```
    """

    def _correct_lookup_field_type(self, view_name, lookup_field):
        assert isinstance(lookup_field, dict) or isinstance(lookup_field, str), (
            f"{view_name} `.lookup_fields` attribute values must be either `str` or `dict` "
            f"types, set the view correctly."
        )

    def pk_exists(self):
        """
        Utility function that checks if `lookup_fields` true pk values are present in the given kwargs.
        """

        lookup_fields = self.lookup_fields if self.lookup_fields else {}

        if not lookup_fields:  # Lookup_fields attribute was not set
            return False

        for lookup_url_kwarg, lookup_field in lookup_fields.items():
            self._correct_lookup_field_type(view_name=self.__class__.__name__, lookup_field=lookup_field)

            if isinstance(lookup_field, dict):
                pk = lookup_field["pk"]
                if pk and self.kwargs.get(lookup_url_kwarg, None) is None:
                    return False
        return True

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        This method should always be used rather than accessing `self.queryset`
        directly, as `self.queryset` gets evaluated only once, and those results
        are cached for all subsequent requests.

        (Eg. return a list of items that is specific to the user)
        """

        queryset = self.queryset

        assert queryset is not None, (
            f"'{self.__class__.__name__}' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
        )

        # Perform the lookup filtering.
        lookup_fields = self.lookup_fields if self.lookup_fields else {}
        filter_kwargs = {}

        for lookup_url_kwarg, lookup_field in lookup_fields.items():
            self._correct_lookup_field_type(view_name=self.__class__.__name__, lookup_field=lookup_field)

            pk = False
            filter_kwarg = None

            if isinstance(lookup_field, dict):
                pk = lookup_field["pk"]
                filter_kwarg = lookup_field["filter_kwarg"]

            elif isinstance(lookup_field, str):
                filter_kwarg = lookup_field

            if not pk:
                assert lookup_url_kwarg in self.kwargs, (
                    f"Expected view {self.__class__.__name__} to be called with a URL keyword argument "
                    f"named '{lookup_url_kwarg}'. Fix your URL conf, or set the `.lookup_fields` "
                    f"attribute on the view correctly."
                )
                filter_kwargs[filter_kwarg] = self.kwargs[lookup_url_kwarg]
            elif pk and self.kwargs.get(lookup_url_kwarg, None) is not None:
                filter_kwargs[filter_kwarg] = self.kwargs[lookup_url_kwarg]

        return queryset.filter(**filter_kwargs)  # filter queryset

    def get_object(self):
        """
        Returns the object the view is displaying.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_fields = self.lookup_fields if self.lookup_fields else {}
        pk_filter_kwargs = {}

        for lookup_url_kwarg, lookup_field in lookup_fields.items():
            self._correct_lookup_field_type(view_name=self.__class__.__name__, lookup_field=lookup_field)
            if isinstance(lookup_field, dict):
                if lookup_field["pk"]:
                    assert lookup_url_kwarg in self.kwargs, (
                        f"Expected view {self.__class__.__name__} to be called with a URL keyword argument "
                        f"named '{lookup_url_kwarg}'. Fix your URL conf, or set the `.lookup_fields` "
                        f"attribute on the view correctly."
                    )
                    pk_filter_kwargs[lookup_field["filter_kwarg"]] = self.kwargs[lookup_url_kwarg]

        assert pk_filter_kwargs, (
            f"{self.__class__.__name__} `.lookup_fields` attribute values must have at least one 'pk':True "
            f"in order to retreive object, set the `.lookup_fields` attribute on the view correctly."
        )

        obj = get_object_or_404(queryset, **pk_filter_kwargs)  # Lookup the object

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
