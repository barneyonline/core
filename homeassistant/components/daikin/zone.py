from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

from . import DOMAIN as DAIKIN_DOMAIN, DaikinApi


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Daikin zone climate based on config_entry."""
    daikin_api: DaikinApi = hass.data[DAIKIN_DOMAIN][entry.entry_id]
    if zones := daikin_api.device.zones:
        async_add_entities(
            [
                DaikinZoneClimateEntity(daikin_api, zone_id, entry.entry_id)
                for zone_id, zone in enumerate(zones)
                if zone[0] != "-" and zone[2] != 0
            ],
            True,
        )


class DaikinZoneClimateEntity(ClimateEntity):
    """Representation of a Daikin zone climate entity."""

    def __init__(self, daikin_api: DaikinApi, zone_id: int, entry_id: str) -> None:
        """Initialize the zone."""
        self._api = daikin_api
        self._zone_id = zone_id
        self._entry_id = entry_id

        # The Daikin system's global target temp
        self._target_temperature = self._api.device.target_temperature

        # Check if the zone actually supports temperature control
        if (
            len(self._api.device.zones[self._zone_id]) < 3
            or self._api.device.zones[self._zone_id][2] == 0
        ):
            raise IndexError("Zone does not have temperature control")

        # Current zone temperature
        self._current_temperature = self._api.device.zones[self._zone_id][2]

        # Make each zone a separate "device" in Home Assistant
        # so that device actions appear in the Automation UI.
        self._attr_device_info = {
            "identifiers": {
                (DAIKIN_DOMAIN, f"{self._api.device.mac}_zone_{self._zone_id}")
            },
            "name": f"{self._api.device.zones[self._zone_id][0]} climate",
            "manufacturer": "Daikin",
            "model": "AirBase",
            "via_device": (DAIKIN_DOMAIN, self._api.device.mac),
            # Most important for device actions:
            "config_entry_id": self._entry_id,
        }

        self._attr_unique_id = f"{self._api.device.mac}-zone-climate{self._zone_id}"
        self._attr_name = f"{self._api.device.zones[self._zone_id][0]} climate"

        # Minimal climate setup
        self._attr_hvac_modes = [HVAC_MODE_OFF, self._api.device.hvac_mode]
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

        # Set the min and max values for zone control
        self._attr_min_temp = self._target_temperature - 2
        self._attr_max_temp = self._target_temperature + 2

    @property
    def current_temperature(self) -> float:
        """Return the current temperature from the zone."""
        return self._api.device.zones[self._zone_id][2]

    @property
    def target_temperature(self) -> float:
        """Return the set temperature for the zone."""
        return self._target_temperature

    @property
    def hvac_mode(self) -> str:
        """Return current HVAC mode."""
        if not self._api.device.is_on:
            return HVAC_MODE_OFF
        return self._api.device.hvac_mode

    async def async_update(self) -> None:
        """Retrieve the latest state from the device."""
        await self._api.async_update()
        self._current_temperature = self._api.device.zones[self._zone_id][2]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if self._attr_min_temp <= temperature <= self._attr_max_temp:
            await self._api.device.set_zone(
                self._zone_id, "lztemp_h", str(round(temperature))
            )
            self._target_temperature = temperature
            await self.async_update()

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        """Set new hvac mode for the zone (on/off)."""
        if hvac_mode == HVAC_MODE_OFF:
            # Turn off the zone
            if self._api.device.is_on:
                await self._api.device.turn_off_zone(self._zone_id)
        else:
            # Turn on the zone in the desired hvac mode
            if not self._api.device.is_on:
                await self._api.device.turn_on_zone(self._zone_id)
        await self.async_update()
