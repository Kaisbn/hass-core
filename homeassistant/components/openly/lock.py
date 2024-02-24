"""Rently Lock Entity."""
from enum import Enum
from typing import Any

from openly.devices import Hub

from homeassistant.components.lock import LockEntity as BaseLockEntity
from homeassistant.const import ATTR_BATTERY_LEVEL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


class LockStatus(Enum):
    """Enum for lock status."""

    LOCKED = "locked"
    LOCKING = "locking"
    UNLOCKED = "unlocked"
    UNLOCKING = "unlocking"
    JAMMED = "jammed"
    NONE = "none"


class LockEntity(CoordinatorEntity, BaseLockEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator: DataUpdateCoordinator, idx, hub: Hub) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._hub = hub
        self._lock = None
        self._lock_status = None

    async def async_update(self) -> None:
        """Update the entity from the server."""
        self._lock = await self.hass.async_add_executor_job(
            self.coordinator.cloud.get_device, self.idx
        )  # type: ignore[func-returns-value]

        self.update_lock_attrs()

    def update_lock_attrs(self) -> None:
        """Update the lock attributes."""
        if not self._lock:
            raise DeviceNotFoundError
        self._lock_status = self._lock.lock_status
        self._attr_is_locked = self._lock_status is LockStatus.LOCKED
        self._attr_is_jammed = self._lock_status is LockStatus.JAMMED
        self._attr_is_locking = self._lock_status is LockStatus.LOCKING
        self._attr_is_unlocking = self._lock_status is LockStatus.UNLOCKING
        self._attr_extra_state_attributes = {
            ATTR_BATTERY_LEVEL: self._lock.status.battery
        }

    def lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        if not self._lock:
            raise DeviceNotFoundError
        # Set status
        self._lock.lock()
        # Send update request
        self._hub.update(self._lock)

        self._lock_status = LockStatus.LOCKING

    def unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        if not self._lock:
            raise DeviceNotFoundError
        # Set status
        self._lock.unlock()
        # Send update request
        self.coordinator.cloud.update_device_status(self._lock)

        self._lock_status = LockStatus.UNLOCKING


class DeviceNotFoundError(HomeAssistantError):
    """Error to indicate device not found."""
