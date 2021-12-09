"""Constants."""
# Template Limits
MAX_MAPPINGS = 200
"""Max number of Mappings permitted in a Template."""

MAX_OUTPUTS = 200
"""Max number of Outputs permitted in a Template."""

MAX_PARAMETERS = 200
"""Max number of Parameters permitted in a Template."""

MAX_RESOURCES = 500
"""Max number of Resources permitted in a Template."""

PARAMETER_TITLE_MAX = 255
"""Max length of a Template Parameter's title."""

TITLE_REGEX = r"^[a-zA-Z0-9]+$"
"""Regex used to validate title used in a Template."""

SERVERLESS_TRANSFORM = "AWS::Serverless-2016-10-31"
