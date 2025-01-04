# custom_components/octotelematics/const.py
"""Constants for the OCTO Telematics integration."""
from datetime import timedelta

DOMAIN = "octotelematics"
DEFAULT_SCAN_INTERVAL = 1440  # minutes
SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

URLS = {
    "base": "https://www.octotelematics.it/octo",
    "login": "https://www.octotelematics.it/octo/login.jsp",
    "login_post": "https://www.octotelematics.it/octo/login",
}

