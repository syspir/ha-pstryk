# Twoje-Miasto Sp. z o.o. / Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-28

"""Constants for the Pstryk Energy integration."""

from datetime import timedelta

DOMAIN = "pstryk"

# API
API_BASE_URL = "https://api.pstryk.pl"
UNIFIED_METRICS_URL = f"{API_BASE_URL}/integrations/meter-data/unified-metrics/"
PRICING_URL = f"{API_BASE_URL}/integrations/pricing/"
PROSUMER_PRICING_URL = f"{API_BASE_URL}/integrations/prosumer-pricing/"

# Config
CONF_API_TOKEN = "api_token"
CONF_IS_PROSUMER = "is_prosumer"
CONF_TIMEZONE = "timezone"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval"

# Defaults
DEFAULT_TIMEZONE = "Europe/Warsaw"
DEFAULT_SCAN_INTERVAL = 15  # minutes
DEFAULT_NAME = "Pstryk"

# Update intervals
UPDATE_INTERVAL_METRICS = timedelta(minutes=15)
UPDATE_INTERVAL_PRICING = timedelta(minutes=45)

# Metrics
METRIC_METER_VALUES = "meter_values"
METRIC_COST = "cost"
METRIC_PRICING = "pricing"
ALL_METRICS = f"{METRIC_METER_VALUES},{METRIC_COST},{METRIC_PRICING}"

# API date format
API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Resolution
RESOLUTION_HOUR = "hour"
RESOLUTION_DAY = "day"
RESOLUTION_MONTH = "month"

# Attribution
ATTRIBUTION = "Dane dostarczone przez Pstryk"

# Panel
CONF_ENABLE_PANEL = "enable_panel"
PANEL_URL = "pstryk-energy"
PANEL_ICON = "mdi:flash"
PANEL_TITLE = "Pstryk Energy"

# Platforms
PLATFORMS = ["sensor"]
