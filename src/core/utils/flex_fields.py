from django.conf import settings
from rest_framework import serializers


# ! This is mostly for swagger documentation purposes
class FlexFieldsQuerySerializer(serializers.Serializer):
    """
    Custom serializer used to represent flex field query parameters
    """

    # TODO figure out a better way than using locals
    locals()[settings.REST_FLEX_FIELDS["EXPAND_PARAM"]] = serializers.ListField(
        child=serializers.ChoiceField(choices=()),
        allow_empty=False,
        required=False,
        help_text="Consists of response fields. Note: not all fields are always supported.",
    )
    locals()[settings.REST_FLEX_FIELDS["OMIT_PARAM"]] = serializers.ListField(
        child=serializers.ChoiceField(choices=()),
        allow_empty=False,
        required=False,
        help_text="Consists of response fields. Note: not all fields are always supported.",
    )
    locals()[settings.REST_FLEX_FIELDS["FIELDS_PARAM"]] = serializers.ListField(
        child=serializers.ChoiceField(choices=()),
        allow_empty=False,
        required=False,
        help_text="Consists of response fields. Note: not all fields are always supported.",
    )


def get_flex_serializer_config(request) -> dict:
    """
    Returns a dict representing configuration that are passed to FlexFieldsModelSerializer
    """
    settings_flex_fields = settings.REST_FLEX_FIELDS
    fields = request.query_params.getlist(settings_flex_fields["FIELDS_PARAM"], None)
    omit = request.query_params.getlist(settings_flex_fields["OMIT_PARAM"], None)
    expand = request.query_params.getlist(settings_flex_fields["EXPAND_PARAM"], None)
    config = {}

    if fields is not None:
        config[settings_flex_fields["FIELDS_PARAM"]] = fields
    if omit is not None:
        config[settings_flex_fields["OMIT_PARAM"]] = omit
    if expand is not None:
        config[settings_flex_fields["EXPAND_PARAM"]] = expand

    return config
