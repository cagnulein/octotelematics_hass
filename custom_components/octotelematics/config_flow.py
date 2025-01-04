"""Config flow for OCTO Telematics integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)

class OctoTelematicsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OCTO Telematics."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the credentials here if possible
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )
            except Exception as err:
                _LOGGER.error("Failed to setup integration: %s", err)
                errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
