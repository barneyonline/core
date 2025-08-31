"""Sensors for Yardian integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YardianUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yardian sensors."""
    coordinator: YardianUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = [
        YardianRainDelaySensor(coordinator),
        YardianActiveZoneCountSensor(coordinator),
        YardianSensorDelaySensor(coordinator),
        YardianWaterHammerDurationSensor(coordinator),
        YardianRegionSensor(coordinator),
    ]

    async_add_entities(entities)


class _BaseYardianSensor(CoordinatorEntity[YardianUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info


class YardianRainDelaySensor(_BaseYardianSensor):
    """Remaining rain delay in seconds."""

    _attr_translation_key = "rain_delay"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-rain-delay"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data.oper_info.get("iRainDelay")
        if isinstance(val, int):
            return val
        return None


class YardianActiveZoneCountSensor(_BaseYardianSensor):
    """Number of zones currently running."""

    _attr_translation_key = "active_zone_count"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-active-zone-count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.active_zones)


class YardianSensorDelaySensor(_BaseYardianSensor):
    """Sensor delay duration in seconds (diagnostic)."""

    _attr_translation_key = "sensor_delay"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-sensor-delay"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data.oper_info.get("iSensorDelay")
        if isinstance(val, int):
            return val
        return None


class YardianWaterHammerDurationSensor(_BaseYardianSensor):
    """Water hammer duration in seconds (diagnostic)."""

    _attr_translation_key = "water_hammer_duration"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-water-hammer-duration"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data.oper_info.get("iWaterHammerDuration")
        if isinstance(val, int):
            return val
        return None


class YardianRegionSensor(_BaseYardianSensor):
    """Region text (diagnostic)."""

    _attr_translation_key = "region"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: YardianUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.yid}-region"

    @property
    def native_value(self) -> str | None:
        val = self.coordinator.data.oper_info.get("region")
        if isinstance(val, str) and val:
            return val
        return None
