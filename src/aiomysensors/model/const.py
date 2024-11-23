"""Provide shared model constants."""

from marshmallow import fields, validate

BROADCAST_ID = 255
DEFAULT_PROTOCOL_VERSION = "1.4"
MAX_NODE_ID = 254
NODE_ID_FIELD = fields.Int(
    required=True,
    validate=validate.Range(
        min=0,
        max=BROADCAST_ID,
        error="Not valid node_id: {input}",
    ),
)
SYSTEM_CHILD_ID = 255
