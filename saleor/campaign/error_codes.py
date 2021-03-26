from enum import Enum


class CampaignErrorCode(Enum):
    INVALID = "invalid"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    UNIQUE = "unique"
    REQUIRED = "required"
