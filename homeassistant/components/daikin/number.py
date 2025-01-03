"""Support for Daikin AirBase zone temperatures."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import DaikinEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daikin zone temperatures based on the config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device = coordinator.device
    zones = getattr(device, "zones", None)

    if not zones:
        _LOGGER.debug("No zones found on Daikin device.")
        return

    _LOGGER.debug("Detected zones: %s", zones)

    entities = []
    for zone_id, zone in enumerate(zones):
        # Example checks: skip if zone name is "-" or zone temperature is 0
        if zone[0] != "-" and zone[2] != 0:
            entities.append(DaikinZoneTemperature(coordinator, zone_id))

    async_add_entities(entities, update_before_add=True)


class DaikinZoneTemperature(DaikinEntity, NumberEntity):
    """Representation of a Daikin zone temperature entity."""

    _attr_icon = "mdi:thermostat"
    _attr_native_step = 1
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, zone_id: int) -> None:
        """Initialize the zone entity."""
        super().__init__(coordinator)
        self._zone_id = zone_id

        # Unique ID: "mac-zone-temp#"
        self._attr_unique_id = f"{self.device.mac}-zone-temp{zone_id}"

        # If you want to show a human-readable name (beyond the device name):
        zone_name = self.device.zones[zone_id][0]
        self._attr_name = f"{zone_name} temperature"

        # Set a default/initial target temperature
        self._target_temperature = 22
        try:
            self._target_temperature = self.device.target_temperature
        except AttributeError:
            _LOGGER.debug("Using default target temperature of 22.")

        # Read the current zone temperature
        try:
            self._current_value = self.device.zones[self._zone_id][2]
        except (IndexError, KeyError):
            _LOGGER.error("Failed to retrieve zone temperature, using default value.")
            self._current_value = self._target_temperature

        # Example: allow up to 2°C above the device's "target_temperature"
        self._attr_native_max_value = self._target_temperature + 2

    @property
    def native_value(self) -> float:
        """Return the current zone temperature."""
        try:
            self._current_value = self.device.zones[self._zone_id][2]
        except (IndexError, KeyError):
            _LOGGER.error("Failed to update zone temperature; using last known value.")
        return self._current_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the zone temperature."""
        min_val = self._attr_native_min_value or 0
        max_val = self._attr_native_max_value or 99

        if not (min_val <= value <= max_val):
            raise HomeAssistantError(
                f"Value {value} out of range ({min_val}-{max_val})."
            )

        self._current_value = value
        retries = 3

        for attempt in range(retries):
            try:
                # Example: setting the zone temperature
                await self.device.set_zone(
                    self._zone_id, "lztemp_h", str(round(self._current_value))
                )
                _LOGGER.debug(
                    "Successfully set temperature for zone %s to %s",
                    self._zone_id,
                    self._current_value,
                )
                break
            except (IndexError, KeyError, AttributeError) as err:
                _LOGGER.error(
                    "Attempt %s: Failed to set zone temperature: %s",
                    attempt + 1,
                    err,
                )
                if attempt == retries - 1:
                    raise HomeAssistantError(
                        f"Failed to set zone temperature after {retries} attempts: {err}"
                    ) from err
                await asyncio.sleep(1)  # brief delay before retrying
