"""Data update coordinator for OCTO Telematics."""
import logging
from datetime import timedelta
import async_timeout
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

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

    async def _async_update_data(self):
        """Fetch data from OCTO Telematics."""
        try:
            async with async_timeout.timeout(30):
                if not self._cookies:
                    await self._login()

                # Get statistics page
                async with self._session.get(
                    f"{URLS['base']}/clienti/consumiCustomer.jsp",
                    cookies=self._cookies
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed("Failed to get statistics")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find kilometers section
                    stats_div = soup.find('div', {'id': 'statPage2'})
                    if not stats_div:
                        raise UpdateFailed("Could not find statistics div")

                    # Find KM
                    total_km = None
                    km_rows = stats_div.find_all('tr', attrs={'align': 'center'})
                    for row in km_rows:
                        text = row.get_text(strip=True)
                        if 'KM TOTALI PERCORSI' in text:
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                total_km = int(numbers[-1])
                                break

                    if not total_km:
                        raise UpdateFailed("Could not find KM value")

                    # Find end date
                    update_date = None
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
                                            update_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                            break
                                        except Exception as err:
                                            _LOGGER.error("Error parsing date: %s", err)
                        if update_date:
                            break

                    if not update_date:
                        update_date = "Unknown"

                    return {
                        "total_km": total_km,
                        "updated_at": update_date
                    }

        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout error") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _login(self):
        """Login to OCTO Telematics."""
        try:
            # Get initial cookies
            async with self._session.get("https://www.octotelematics.it/octo/login.jsp") as response:
                if response.status != 200:
                    raise ConfigEntryAuthFailed("Failed to access login page")
                
            # Perform login
            login_data = {
                "UserName": self._username,
                "UserPassword": self._password
            }
            
            async with self._session.post(
                "https://www.octotelematics.it/octo/login",
                data=login_data,
                allow_redirects=True
            ) as response:
                if response.status != 200:
                    raise ConfigEntryAuthFailed("Invalid credentials")
                
                self._cookies = {cookie.key: cookie.value for cookie in response.cookies.values()}

        except aiohttp.ClientError as err:
            raise ConfigEntryAuthFailed(f"Failed to login: {err}")

    async def _get_stats(self):
        """Get vehicle statistics."""
        try:
            async with self._session.get(
                "https://www.octotelematics.it/octo/assicurazioni/statistics.jsp",
                cookies=self._cookies
            ) as response:
                if response.status != 200:
                    raise UpdateFailed("Failed to get statistics")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find the total kilometers element
                km_element = soup.find(text="KM TOTALI PERCORSI:")
                if km_element:
                    km_value = km_element.find_next(text=True).strip()
                    try:
                        total_km = float(km_value.replace(',', ''))
                        return {"total_km": total_km}
                    except ValueError:
                        raise UpdateFailed(f"Failed to parse kilometers value: {km_value}")
                
                raise UpdateFailed("Could not find kilometers data")

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching statistics: {err}")

