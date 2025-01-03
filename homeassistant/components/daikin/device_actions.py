"""Provides device actions for Daikin AC."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
# Import your integration domain for custom services (e.g., "daikin_airbase")
from . import DOMAIN as DAIKIN_DOMAIN

# Constants for optional fields
CONF_ZONE_ID = "zone_id"
CONF_TEMPERATURE = "temperature"

# Add a new action type for setting a zone temperature
ACTION_TYPES = {"turn_on", "turn_off", "set_zone_temperature"}

# Use the climate domain in the action schema,
# since your entity is climate.daikinap02966
ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_domain("climate"),
        vol.Optional(CONF_ZONE_ID): cv.positive_int,
        vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
    }
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Daikin AC devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        # Skip anything that isn't a climate entity
        if entry.domain != "climate":
            continue

        base_action = {
            CONF_DEVICE_ID: device_id,
            # For the device action, this must match the entity's domain
            CONF_DOMAIN: "climate",
            CONF_ENTITY_ID: entry.entity_id,
        }

        # Add actions for turn_on / turn_off
        actions.append({**base_action, CONF_TYPE: "turn_on"})
        actions.append({**base_action, CONF_TYPE: "turn_off"})

        # Add action for set_zone_temperature
        actions.append({**base_action, CONF_TYPE: "set_zone_temperature"})

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    action_type = config[CONF_TYPE]

    if action_type == "set_zone_temperature":
        zone_id = config.get(CONF_ZONE_ID)
        temperature = config.get(CONF_TEMPERATURE)

        if zone_id is None or temperature is None:
            # Could raise an error if the user didn't provide required fields
            return

        # Call your custom Daikin AirBase service
        service_data = {
            "zone_id": zone_id,
            "temperature": temperature,
        }
        await hass.services.async_call(
            DAIKIN_DOMAIN,           # e.g. "daikin_airbase"
            "set_zone_temperature",  # your custom service
            service_data,
            blocking=True,
            context=context,
        )
        return

    # Handle turn_on / turn_off for a climate entity
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if action_type == "turn_on":
        service = SERVICE_TURN_ON  # This may need to map to climate.set_hvac_mode
    elif action_type == "turn_off":
        service = SERVICE_TURN_OFF # This may need to map to climate.set_hvac_mode off
    else:
        return

    # Call the climate domain service
    await hass.services.async_call(
        "climate",  # Because our entity is in the climate domain
        service,
        service_data,
        blocking=True,
        context=context,
    )
