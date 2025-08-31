"""Diagnostics support for Yardian integration."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import YardianUpdateCoordinator

TO_REDACT = {
    "access_token",
    "host",
    "serialNumber",
    "yid",
    "sIotcUid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator: YardianUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    device = {
        "name": entry.title,
        "model": coordinator._model,
        "yid": coordinator.yid,
        "serialNumber": coordinator._serial,
    }

    # Sanitize zones to basic tuple [name, enabled]
    zones = []
    for idx, z in enumerate(data.zones):
        try:
            zones.append([z[0], z[1]])
        except Exception:
            zones.append([None, None])

    payload = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "device": async_redact_data(device, TO_REDACT),
        "state": {
            "active_zones": sorted(list(data.active_zones)),
            "zones": zones,
        },
        "oper_info": async_redact_data(data.oper_info, TO_REDACT),
    }

    return payload
