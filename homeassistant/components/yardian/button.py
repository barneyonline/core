"""Buttons for Yardian integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YardianUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yardian buttons."""
    coordinator: YardianUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([YardianStopAllButton(coordinator)])


class YardianStopAllButton(CoordinatorEntity[YardianUpdateCoordinator], ButtonEntity):
    """Button to stop all irrigation."""

    _attr_has_entity_name = True
    _attr_translation_key = "stop_all_irrigation"

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        """Initialize stop all irrigation button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-stop"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Handle the button press to stop irrigation and refresh state."""
        await self.coordinator.controller.stop_irrigation()
        await self.coordinator.async_request_refresh()
