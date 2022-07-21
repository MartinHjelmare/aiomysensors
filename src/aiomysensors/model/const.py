"""Provide shared model constants."""
from marshmallow import fields, validate

from .protocol import BROADCAST_ID

NODE_ID_FIELD = fields.Int(
    required=True,
    validate=validate.Range(
        min=0,
        max=BROADCAST_ID,
        error="Not valid node_id: {input}",
    ),
)
