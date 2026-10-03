"""Shared helpers for Talk field models.

Talk models are allowlists: ``from_controller`` copies only the declared
fields, so controller-only secrets (``sip_password``, ``hashed_key``, API
keys, permission scopes) never reach a tool response.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="TalkModel")


class TalkModel(BaseModel):
    """Base for read-only Talk models; unknown controller fields are dropped."""

    model_config = ConfigDict(extra="ignore")


def ro(description: str, default: Any = None) -> Any:
    """Declare a read-only field."""
    return Field(default=default, description=description, json_schema_extra={"mutable": False})


def as_dict(raw: Any) -> dict[str, Any]:
    return raw if isinstance(raw, dict) else {}


def build(model: type[T], data: dict[str, Any]) -> T:
    """Validate ``data`` into ``model``, dropping fields whose type is unexpected.

    Talk's API is undocumented and its field types drift between releases and
    even between rows. One surprising value must not fail a whole list, so an
    offending top-level field is omitted (and its name logged) instead.
    """
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        bad = {str(error["loc"][0]) for error in exc.errors() if error.get("loc")}
        logger.warning("[talk-models] %s: dropping fields with unexpected types: %s", model.__name__, sorted(bad))
        return model.model_validate({key: value for key, value in data.items() if key not in bad})
