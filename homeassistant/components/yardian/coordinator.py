"""Update coordinators for Yardian."""

from __future__ import annotations

import asyncio
import datetime
import logging

from pyyardian import (
    AsyncYardianClient,
    NetworkException,
    NotAuthorizedException,
    YardianDeviceState,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(seconds=30)


class YardianUpdateCoordinator(DataUpdateCoordinator[YardianDeviceState]):
    """Coordinator for Yardian API calls."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        controller: AsyncYardianClient,
    ) -> None:
        """Initialize Yardian API communication."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )

        self.controller = controller
        self._yid = entry.data["yid"]
        self._name = entry.title
        self._model = entry.data["model"]
        self._serial_number = entry.data.get("serialNumber")
        self.oper_info: OperationInfo | None = None

    @property
    def yid(self) -> str:
        """Return the controller unique id."""
        return self._yid

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        info = DeviceInfo(
            name=self._name,
            identifiers={(DOMAIN, self._yid)},
            manufacturer=MANUFACTURER,
            model=self._model,
        )
        if self._serial_number:
            info["serial_number"] = self._serial_number
        return info

    @property
    def serial_number(self) -> str | None:
        """Return the controller serial number."""
        return self._serial_number

    async def _async_update_data(self) -> YardianDeviceState:
        """Fetch data from Yardian device."""
        try:
            async with asyncio.timeout(10):
                self.oper_info = await self.controller.fetch_oper_info()
                if not self._serial_number:
                    device_info = await self.controller.fetch_device_info()
                    self._serial_number = device_info.get("serialNumber")
                return await self.controller.fetch_device_state()

        except TimeoutError as e:
            raise UpdateFailed("Communication with Device was time out") from e
        except NotAuthorizedException as e:
            raise UpdateFailed("Invalid access token") from e
        except NetworkException as e:
            raise UpdateFailed("Failed to communicate with Device") from e
