"""Rently Hub Entity."""
from openly.devices import Hub
from openly.devices.base_device import BaseDevice

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


class HubEntity(CoordinatorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator: DataUpdateCoordinator, idx: str, hub: Hub) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx: str = idx
        self._hub: Hub = hub
        self._devices: list[BaseDevice] = []

    @property
    def devices(self) -> list[BaseDevice]:
        """Return list of devices."""
        return self._devices

    def update_device(self, device: BaseDevice):
        """Return cloud."""
        return self.coordinator.cloud.update_device_status(self, device)

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """
        self._hub = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.cloud.get_hub, self.idx
        )

        # Get list of devices
        self._devices = await self.hass.async_add_executor_job(
            self.coordinator.cloud.get_devices, self.idx
        )
