"""Test Yardian entities setup and behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.yardian.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.const import EntityCategory
from pyyardian.async_client import YardianDeviceState

from tests.common import MockConfigEntry


class FakeYardianClient:
    """Fake AsyncYardianClient for tests."""

    def __init__(self, *_: object, **__: object) -> None:
        """Initialize fake client with mocked stop_irrigation."""
        self.stop_irrigation = AsyncMock()

    async def fetch_device_state(self):  # pyyardian.YardianDeviceState-like
        """Return fake YardianDeviceState with three zones and one active."""
        zones = [["Zone 1", 1], ["Zone 2", 0], ["Zone 3", 1]]
        active_zones = {0}
        return YardianDeviceState(zones=zones, active_zones=active_zones)

    async def fetch_oper_info(self):
        """Return fake operation info."""
        return {
            "iRainDelay": 3600,
            "iStandby": 0,
            "fFreezePrevent": 1,
            "iSensorDelay": 5,
            "iWaterHammerDuration": 2,
            "region": "US",
        }


@pytest.mark.asyncio
async def test_entities_and_button_press(hass: HomeAssistant) -> None:
    """Test entities are created and button triggers stop."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Binary sensor: watering running
    bs_entity_id = ent_reg.async_get_entity_id(
        "binary_sensor", DOMAIN, "yid123-watering-running"
    )
    assert bs_entity_id is not None
    bs = hass.states.get(bs_entity_id)
    assert bs.state == "on"
    assert bs.attributes.get("device_class") == "running"

    # Sensor: rain delay
    rain_entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, "yid123-rain-delay")
    assert rain_entity_id is not None
    rain = hass.states.get(rain_entity_id)
    assert rain.state == "3600"
    assert rain.attributes.get("device_class") == "duration"
    assert rain.attributes.get("unit_of_measurement") == "s"
    assert rain.attributes.get("state_class") == "measurement"

    # Sensor: active zone count
    azc_entity_id = ent_reg.async_get_entity_id(
        "sensor", DOMAIN, "yid123-active-zone-count"
    )
    assert azc_entity_id is not None
    azc = hass.states.get(azc_entity_id)
    assert azc.state == "1"
    assert azc.attributes.get("state_class") == "measurement"

    # Button: stop all irrigation
    stop_entity_id = ent_reg.async_get_entity_id("button", DOMAIN, "yid123-stop")
    assert stop_entity_id is not None

    # Press button and assert client called
    fake_client: FakeYardianClient = hass.data[DOMAIN][entry.entry_id].controller  # type: ignore[attr-defined]
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {"entity_id": stop_entity_id},
        blocking=True,
    )
    fake_client.stop_irrigation.assert_awaited_once()

    # Device info includes serial number
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, "yid123")})
    assert device is not None
    assert device.serial_number == "SN1"


@pytest.mark.asyncio
async def test_binary_sensors_state(hass: HomeAssistant) -> None:
    """Test standby and freeze_prevent binary sensors reflect oper_info."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    standby_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, "yid123-standby")
    freeze_id = ent_reg.async_get_entity_id(
        "binary_sensor", DOMAIN, "yid123-freeze-prevent"
    )
    assert standby_id and freeze_id
    assert hass.states.get(standby_id).state == "off"
    assert hass.states.get(freeze_id).state == "on"
    standby_entry = ent_reg.async_get(standby_id)
    freeze_entry = ent_reg.async_get(freeze_id)
    assert standby_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert freeze_entry.entity_category is EntityCategory.DIAGNOSTIC


@pytest.mark.asyncio
async def test_enable_diagnostic_sensors_values(hass: HomeAssistant) -> None:
    """Enable diagnostic sensors and assert values and units."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Enable diagnostic sensors
    for uid in ("yid123-sensor-delay", "yid123-water-hammer-duration", "yid123-region"):
        eid = ent_reg.async_get_entity_id("sensor", DOMAIN, uid)
        ent_reg.async_update_entity(eid, disabled_by=None)

    # Reload entry to apply registry changes
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Assert values and attributes
    sensor_delay = hass.states.get(
        ent_reg.async_get_entity_id("sensor", DOMAIN, "yid123-sensor-delay")
    )
    water_hammer = hass.states.get(
        ent_reg.async_get_entity_id("sensor", DOMAIN, "yid123-water-hammer-duration")
    )
    region = hass.states.get(
        ent_reg.async_get_entity_id("sensor", DOMAIN, "yid123-region")
    )

    assert sensor_delay.state == "5"
    assert sensor_delay.attributes.get("device_class") == "duration"
    assert sensor_delay.attributes.get("unit_of_measurement") == "s"
    assert sensor_delay.attributes.get("state_class") == "measurement"

    assert water_hammer.state == "2"
    assert water_hammer.attributes.get("device_class") == "duration"
    assert water_hammer.attributes.get("unit_of_measurement") == "s"

    assert region.state == "US"


@pytest.mark.asyncio
async def test_enable_zone_enabled_entity_and_state(hass: HomeAssistant) -> None:
    """Enable a per-zone enabled binary sensor and check its state."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    eid = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, "yid123-zone-enabled-0")
    ent_reg.async_update_entity(eid, disabled_by=None)

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(eid)
    assert state is not None and state.state == "on"


@pytest.mark.asyncio
async def test_button_press_triggers_refresh(hass: HomeAssistant) -> None:
    """Pressing the stop button triggers a coordinator refresh."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    stop_entity_id = ent_reg.async_get_entity_id("button", DOMAIN, "yid123-stop")
    assert stop_entity_id is not None

    coordinator = hass.data[DOMAIN][entry.entry_id]
    with patch.object(
        coordinator, "async_request_refresh", new=AsyncMock()
    ) as mocked_refresh:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            "press",
            {"entity_id": stop_entity_id},
            blocking=True,
        )
        mocked_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_disabled_by_default_entities(hass: HomeAssistant) -> None:
    """Verify diagnostic entities are disabled by default in the registry."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.2.3.4",
            "access_token": "abc",
            "name": "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
        unique_id="yid123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.yardian.__init__.AsyncYardianClient",
        return_value=FakeYardianClient(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Per-zone enabled sensors (for 3 zones created in FakeYardianClient)
    for idx in range(3):
        eid = ent_reg.async_get_entity_id(
            "binary_sensor", DOMAIN, f"yid123-zone-enabled-{idx}"
        )
        assert eid is not None
        reg_entry = ent_reg.async_get(eid)
        assert reg_entry is not None and reg_entry.disabled
        assert reg_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert reg_entry.entity_category is EntityCategory.DIAGNOSTIC

    # Diagnostic sensors disabled by default
    for dom, uid in (
        ("sensor", "yid123-sensor-delay"),
        ("sensor", "yid123-water-hammer-duration"),
        ("sensor", "yid123-region"),
    ):
        eid = ent_reg.async_get_entity_id(dom, DOMAIN, uid)
        assert eid is not None
        reg_entry = ent_reg.async_get(eid)
        assert reg_entry is not None and reg_entry.disabled
        assert reg_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert reg_entry.entity_category is EntityCategory.DIAGNOSTIC
