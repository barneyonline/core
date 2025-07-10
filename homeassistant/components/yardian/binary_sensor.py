"""Yardian binary sensor platform."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YardianUpdateCoordinator


@dataclass
class YardianBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Yardian binary sensor."""

    value_fn: Callable[[YardianUpdateCoordinator], bool | None]


SENSORS: tuple[YardianBinarySensorDescription, ...] = (
    YardianBinarySensorDescription(
        key="freeze_prevent",
        translation_key="freeze_prevent",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: (
            bool(coord.oper_info.get("fFreezePrevent")) if coord.oper_info else None
        ),
    ),
    YardianBinarySensorDescription(
        key="standby",
        translation_key="standby",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: (
            bool(coord.oper_info.get("iStandby")) if coord.oper_info else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yardian binary sensors."""
    coordinator: YardianUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        YardianBinarySensor(coordinator, description) for description in SENSORS
    )


class YardianBinarySensor(
    CoordinatorEntity[YardianUpdateCoordinator], BinarySensorEntity
):
    """Define a Yardian binary sensor."""

    entity_description: YardianBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: YardianUpdateCoordinator,
        description: YardianBinarySensorDescription,
    ) -> None:
        """Initialize Yardian binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.yid}-{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator)
