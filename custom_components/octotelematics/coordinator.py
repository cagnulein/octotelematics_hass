"""Data update coordinator for OCTO Telematics."""
import logging
import asyncio
import re
from datetime import timedelta
import async_timeout
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import URLS

_LOGGER = logging.getLogger(__name__)

class OctoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching OCTO Telematics data."""

    def __init__(self, hass: HomeAssistant, username: str, password: str, scan_interval: int, session: aiohttp.ClientSession):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="OCTO Telematics",
            update_interval=timedelta(minutes=scan_interval),
        )
        self._username = username
        self._password = password
        self._session = session
        self._cookies = {}
        self._last_known_values = {
            "total_km": None,
            "updated_at": "Unknown"
        }
        self._consecutive_failures = 0
        self._max_retries = 3

    async def _extract_km_value(self, stats_div) -> tuple[int, bool]:
        """Extract kilometer value from stats div."""
        try:
            km_rows = stats_div.find_all('tr', attrs={'align': 'center'})
            for row in km_rows:
                text = row.get_text(strip=True)
                if 'KM TOTALI PERCORSI' in text:
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return int(numbers[-1]), True
            return self._last_known_values["total_km"] or 0, False
        except Exception as err:
            _LOGGER.warning("Error extracting KM value: %s", err)
            return self._last_known_values["total_km"] or 0, False

    async def _extract_update_date(self, stats_div) -> tuple[str, bool]:
        """Extract update date from stats div."""
        try:
            all_tables = stats_div.find_all('table')
            for table in all_tables:
                cells = table.find_all('td', {'class': 'inputMask'})
                for i, cell in enumerate(cells):
                    if cell.get_text(strip=True) == 'AL:':
                        if i + 1 < len(cells):
                            date_text = cells[i + 1].get_text(strip=True)
                            if date_text:
                                try:
                                    day, month, year = date_text.split('/')
                                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}", True
                                except Exception as err:
                                    _LOGGER.warning("Error parsing date: %s", err)
            return self._last_known_values["updated_at"], False
        except Exception as err:
            _LOGGER.warning("Error extracting update date: %s", err)
            return self._last_known_values["updated_at"], False

    async def _async_update_data(self):
        """Fetch data from OCTO Telematics."""
        for attempt in range(self._max_retries):
            try:
                async with async_timeout.timeout(30):
                    if not self._cookies:
                        await self._login()

                    # Get statistics page
                    async with self._session.get(
                        f"{URLS['base']}/clienti/consumiCustomer.jsp",
                        cookies=self._cookies
                    ) as response:
                        if response.status == 401:
                            self._cookies = {}  # Clear cookies to force re-login
                            if attempt < self._max_retries - 1:
                                continue
                            raise ConfigEntryAuthFailed("Session expired")
                        
                        if response.status != 200:
                            _LOGGER.warning("Failed to get statistics, status: %s", response.status)
                            if attempt < self._max_retries - 1:
                                continue
                            return self._last_known_values

                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find statistics section
                        stats_div = soup.find('div', {'id': 'statPage2'})
                        if not stats_div:
                            _LOGGER.warning("Statistics div not found in HTML response")
                            if attempt < self._max_retries - 1:
                                continue
                            return self._last_known_values

                        # Extract KM value and update date
                        total_km, km_success = await self._extract_km_value(stats_div)
                        update_date, date_success = await self._extract_update_date(stats_div)

                        # Update last known values if extraction was successful
                        if km_success:
                            self._last_known_values["total_km"] = total_km
                        if date_success:
                            self._last_known_values["updated_at"] = update_date

                        self._consecutive_failures = 0
                        return {
                            "total_km": total_km,
                            "updated_at": update_date
                        }

            except asyncio.TimeoutError as err:
                _LOGGER.warning("Timeout error on attempt %d: %s", attempt + 1, err)
                if attempt == self._max_retries - 1:
                    self._consecutive_failures += 1
                    if self._consecutive_failures > 5:
                        raise UpdateFailed("Multiple consecutive timeout errors")
                    return self._last_known_values
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except ConfigEntryAuthFailed as auth_err:
                raise auth_err  # Always raise auth errors

            except aiohttp.ClientError as err:
                _LOGGER.warning("API communication error on attempt %d: %s", attempt + 1, err)
                if attempt == self._max_retries - 1:
                    return self._last_known_values
                await asyncio.sleep(2 ** attempt)

            except Exception as err:
                _LOGGER.error("Unexpected error on attempt %d: %s", attempt + 1, err)
                if attempt == self._max_retries - 1:
                    return self._last_known_values
                await asyncio.sleep(2 ** attempt)

        return self._last_known_values

    async def _login(self):
        """Login to OCTO Telematics."""
        try:
            # Get initial cookies
            async with self._session.get(URLS["login"]) as response:
                if response.status != 200:
                    raise ConfigEntryAuthFailed("Failed to access login page")
                
            # Perform login
            login_data = {
                "UserName": self._username,
                "UserPassword": self._password
            }
            
            async with self._session.post(
                URLS["login_post"],
                data=login_data,
                allow_redirects=True
            ) as response:
                if response.status != 200:
                    raise ConfigEntryAuthFailed("Invalid credentials")
                
                self._cookies = {cookie.key: cookie.value for cookie in response.cookies.values()}

        except aiohttp.ClientError as err:
            raise ConfigEntryAuthFailed(f"Failed to login: {err}")