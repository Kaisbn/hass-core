"""The Rently integration."""
from __future__ import annotations

from openly.cloud import RentlyCloud
from openly.exceptions import MissingParametersError, RentlyAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .config_flow import API_URL, LOGIN_URL, CannotConnect, InvalidAuth
from .const import DOMAIN
from .coordinator import CloudCoordinator

PLATFORMS: list[Platform] = [Platform.LOCK]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rently from a config entry."""
    cloud = RentlyCloud(
        api_url=API_URL,
        login_url=LOGIN_URL,
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
    # Save as config entry data
    hass.data[DOMAIN][entry.entry_id] = coordinator

    return True
