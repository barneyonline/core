"""Yardian sensor platform."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YardianUpdateCoordinator


@dataclass
class YardianSensorDescription(SensorEntityDescription):
    """Describe a Yardian sensor."""

    value_fn: Callable[[YardianUpdateCoordinator], Any]


SENSORS: tuple[YardianSensorDescription, ...] = (
    YardianSensorDescription(
        key="rain_delay",
        translation_key="rain_delay",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: (
            coord.oper_info.get("iRainDelay") if coord.oper_info else None
        ),
    ),
    YardianSensorDescription(
        key="sensor1",
        translation_key="sensor1",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: (
            coord.oper_info.get("sensor1", {}).get("value") if coord.oper_info else None
        ),
    ),
    YardianSensorDescription(
        key="sensor2",
        translation_key="sensor2",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: (
            coord.oper_info.get("sensor2", {}).get("value") if coord.oper_info else None
        ),
    ),
    YardianSensorDescription(
        key="serial_number",
        translation_key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: coord.serial_number,
    ),
    YardianSensorDescription(
        key="yid",
        translation_key="yid",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coord: coord.yid,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Yardian sensors."""
    coordinator: YardianUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        YardianSensor(coordinator, description) for description in SENSORS
    )


class YardianSensor(CoordinatorEntity[YardianUpdateCoordinator], SensorEntity):
    """Define a Yardian sensor."""

    entity_description: YardianSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: YardianUpdateCoordinator,
        description: YardianSensorDescription,
    ) -> None:
        """Initialize Yardian sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.yid}-{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return the value for the sensor."""
        return self.entity_description.value_fn(self.coordinator)
