from django.conf import settings


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
