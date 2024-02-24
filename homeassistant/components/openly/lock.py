"""Rently Lock Entity."""
from enum import Enum
from typing import Any

from openly.devices import Lock

from homeassistant.components.lock import LockEntity as BaseLockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_BATTERY_LEVEL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Initialize Hub entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(coordinator.locks, update_before_add=True)


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

    _attr_has_entity_name = True
    _attr_name = None
    _lock: Lock = None
    _lock_status: LockStatus = LockStatus.NONE

    def __init__(self, coordinator: DataUpdateCoordinator, idx: str) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx: str = idx

    async def async_update(self) -> None:
        """Update the entity from the server."""
        self._lock = await self.hass.async_add_executor_job(
            self.coordinator.cloud.get_device, self.idx
        )
        if not self._lock:
            raise DeviceNotFoundError

        self._lock_status = self._lock.mode
        self.update_lock_attrs()

    def update_lock_attrs(self) -> None:
        """Update the lock attributes."""
        self._attr_is_locked = self._lock_status is LockStatus.LOCKED
        self._attr_is_jammed = self._lock_status is LockStatus.JAMMED
        self._attr_is_locking = self._lock_status is LockStatus.LOCKING
        self._attr_is_unlocking = self._lock_status is LockStatus.UNLOCKING
        self._attr_extra_state_attributes = {
            ATTR_BATTERY_LEVEL: self._lock.battery,
        }

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        return self._lock.name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.idx)},
            name=self.name,
            manufacturer=self._lock.manufacturer,
            model=self._lock.product_name,
        )

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        return self._lock_status is LockStatus.LOCKED

    @property
    def is_jammed(self) -> bool:
        """Return true ifV lock is jammed."""
        return self._lock_status is LockStatus.JAMMED

    @property
    def is_locking(self) -> bool:
        """Return true if lock is locking."""
        return self._lock_status is LockStatus.LOCKING

    @property
    def is_unlocking(self) -> bool:
        """Return true if lock is unlocking."""
        return self._lock_status is LockStatus.UNLOCKING

    def lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        if not self._lock:
            raise DeviceNotFoundError
        # Set status
        self._lock.lock()
        # Send update request
        self.coordinator.cloud.update_device_status(self._lock)

        self._lock_status = LockStatus.LOCKING
        self.update_lock_attrs()

    def unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        if not self._lock:
            raise DeviceNotFoundError
        # Set status
        self._lock.unlock()
        # Send update request
        self.coordinator.cloud.update_device_status(self._lock)

        self._lock_status = LockStatus.UNLOCKING
        self.update_lock_attrs()


class DeviceNotFoundError(HomeAssistantError):
    """Error to indicate device not found."""
