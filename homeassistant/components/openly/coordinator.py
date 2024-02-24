"""Define a custom coordinator for Rently API communication."""
import asyncio
from datetime import timedelta
import logging

from openly.cloud import RentlyCloud
from openly.exceptions import InvalidResponseError, RentlyAuthError

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .hub import HubEntity

_LOGGER = logging.getLogger(__name__)


class CloudCoordinator(DataUpdateCoordinator):
    """Coordinator for Rently API.."""

    def __init__(self, hass: HomeAssistant, cloud: RentlyCloud) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Rently Hubs",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.cloud = cloud

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with asyncio.timeout(10):
                # Get list of hubs
                res = await self.hass.async_add_executor_job(self.cloud.get_hubs)

                if not hasattr(res, "hubs") or not res["hubs"]:
                    raise UpdateFailed("No hubs found")

                # Create HubCoordinator for each hub
                return [
                    HubEntity(self, hub["id"], hub, self.cloud) for hub in res["hubs"]
                ]
        except RentlyAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except InvalidResponseError as err:
            raise UpdateFailed("Error communicating with API") from err
