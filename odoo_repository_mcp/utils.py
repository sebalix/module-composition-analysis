# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import functools
import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

from odoo.addons.ai_tool.tools import aitool


def _unset_to_none(value):
    """Convert Odoo's unset marker (False) to None."""
    return None if value is False else value


SOURCE_OF_TRUTH_PATTERN = re.compile(r"https?://\S+")


def check_source_of_truth(note):
    """Ensure a note carries at least one source of truth URL.

    High-confidence timelines (created or confirmed through the MCP tools)
    must document the upstream change they rely on: a GitHub commit URL,
    an OpenUpgrade migration script URL, ...
    """
    if not note or not SOURCE_OF_TRUTH_PATTERN.search(note):
        raise ValueError(
            "A source of truth URL is required in 'note' to confirm a "
            "timeline (e.g. the GitHub commit or the OpenUpgrade "
            "migration script URL)."
        )


# Odoo represents the unset values of its string (and serialized) fields
# with False: the tool inputs and outputs carry them as None instead
NullableStr = Annotated[str | None, BeforeValidator(_unset_to_none)]
NullableDict = Annotated[dict | None, BeforeValidator(_unset_to_none)]


def _model_properties(model):
    """Return the JSON schema properties of a Pydantic model, with the
    definitions of the nested models inlined.

    The `aitool` decorator wraps the properties in a root object schema
    without keeping the `$defs` they may refer to, so the references are
    resolved here.
    """
    schema = model.model_json_schema()
    definitions = schema.get("$defs", {})

    def inline(sub_schema):
        if "$ref" in sub_schema:
            name = sub_schema["$ref"].rpartition("/")[2]
            return inline(definitions[name])
        if isinstance(sub_schema.get("properties"), dict):
            sub_schema = {
                **sub_schema,
                "properties": {
                    name: inline(property_schema)
                    for name, property_schema in sub_schema["properties"].items()
                },
            }
        for key in ("items", "additionalProperties"):
            if isinstance(sub_schema.get(key), dict):
                sub_schema = {**sub_schema, key: inline(sub_schema[key])}
        if "anyOf" in sub_schema:
            sub_schema = {
                **sub_schema,
                "anyOf": [inline(item) for item in sub_schema["anyOf"]],
            }
        return sub_schema

    return {
        name: inline(property_schema)
        for name, property_schema in schema.get("properties", {}).items()
    }


def mcp_tool(input_model, output_model):
    """`aitool` decorator taking Pydantic models for the input/output
    schemas of a tool.

    - The JSON schemas exposed to the MCP clients are generated from the
      models (see `_model_properties`).
    - The tool inputs are validated against `input_model`: missing
      required inputs and invalid values return a tool error.
    - The tool output is validated against `output_model` and serialized:
      the unset values become null, and the output is guaranteed to match
      the schema exposed to the clients.
    - Any `ValueError` (including the Pydantic validation ones) follows
      the `{"error": ...}` output convention.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, **kwargs):
            try:
                inputs = input_model(**kwargs)
                result = func(self, **inputs.model_dump())
                return output_model(**result).model_dump(mode="json")
            except ValueError as error:
                return {"error": str(error)}

        return aitool(
            input_schema=_model_properties(input_model),
            output_schema=_model_properties(output_model),
            # The required inputs are the fields without default
            required_inputs=[
                name
                for name, field in input_model.model_fields.items()
                if field.is_required()
            ],
        )(wrapper)

    return decorator


class NoInputs(BaseModel):
    """No input."""
