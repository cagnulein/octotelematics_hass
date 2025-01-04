"""Support for OCTO Telematics sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OCTO Telematics sensor."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([OctoTotalKmSensor(coordinator)], True)

class OctoTotalKmSensor(CoordinatorEntity, SensorEntity):
    """Representation of an OCTO Telematics Total KM sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "OCTO Total Kilometers"
        self._attr_unique_id = f"octo_total_km_{coordinator._username}"
        self._attr_native_unit_of_measurement = "km"
        self._attr_icon = "mdi:car"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("total_km")
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        attrs = {}
        if self.coordinator.data:
            attrs["last_update"] = self.coordinator.data.get("updated_at")
        return attrs

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator._username)},
            "name": "OCTO Telematics Vehicle",
            "manufacturer": "OCTO Telematics",
        }