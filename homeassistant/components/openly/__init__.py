"""The Rently integration."""
from __future__ import annotations

from openly.cloud import RentlyCloud
from openly.devices import Lock
from openly.exceptions import MissingParametersError, RentlyAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_flow import CannotConnect, InvalidAuth
from .coordinator import CloudCoordinator
from .lock import LockEntity

PLATFORMS: list[Platform] = [Platform.LOCK]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Rently from a config entry."""
    cloud = RentlyCloud(
        url="https://app2.keyless.rocks/api",
        login_url="https://remotapp.rently.com/oauth/token",
    )

    try:
        await hass.async_add_executor_job(
            cloud.login, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
        )
    except RentlyAuthError as err:
        raise InvalidAuth from err
    except MissingParametersError as err:
        raise CannotConnect from err

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    coordinator = CloudCoordinator(hass, cloud)
    await coordinator.async_config_entry_first_refresh()

    for hub in coordinator.data:
        await hub.async_update()

        for device in hub.devices:
            if isinstance(device, Lock):
                async_add_entities([LockEntity(coordinator, device.id, hub)])
        async_add_entities(hub.devices, update_before_add=True)

    return True
