"""Provides device actions for Daikin zone climates."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er

# Import your integration domain
from .const import DOMAIN as DAIKIN_DOMAIN

CONF_ZONE_ID = "zone_id"
CONF_TEMPERATURE = "temperature"

ACTION_TYPES = {"set_zone_temperature"}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        # Must be 'climate' because your zone entities are climate.*
        vol.Required(CONF_ENTITY_ID): cv.entity_domain("climate"),
        vol.Optional(CONF_ZONE_ID): cv.positive_int,
        vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
    }
)


async def async_get_actions(hass: HomeAssistant, device_id: str) -> list[dict]:
    """List device actions for Daikin zone climate devices."""
    registry = er.async_get(hass)
    actions = []

    for entry in er.async_entries_for_device(registry, device_id):
        # Our zone climate is domain 'climate'
        if entry.domain != "climate":
            continue

        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DAIKIN_DOMAIN,  # or "climate" if you prefer, but typically it's your integration domain
            CONF_ENTITY_ID: entry.entity_id,
        }

        actions.append({**base_action, CONF_TYPE: "set_zone_temperature"})

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    action_type = config[CONF_TYPE]

    if action_type == "set_zone_temperature":
        # zone_id is optional if we can parse it from the entity or user input
        zone_id = config.get(CONF_ZONE_ID)
        temperature = config.get(CONF_TEMPERATURE)

        if temperature is None:
            return  # or raise an error

        # Simply call the standard climate.set_temperature service:
        service_data = {
            ATTR_ENTITY_ID: config[CONF_ENTITY_ID],
            "temperature": temperature,
        }
        await hass.services.async_call(
            "climate",
            "set_temperature",
            service_data,
            blocking=True,
            context=context,
        )
