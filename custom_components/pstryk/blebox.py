# Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-29

"""BleBox local meter API client for Pstryk Energy."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Scaling factors for BleBox multiSensor values
BLEBOX_SCALE = {
    "voltage": 10,
    "current": 1000,
    "frequency": 1000,
    "forwardActiveEnergy": 1000,
    "reverseActiveEnergy": 1000,
    "forwardReactiveEnergy": 1000,
    "reverseReactiveEnergy": 1000,
    "apparentEnergy": 1000,
}


class PstrykBleBoxError(Exception):
    """BleBox connection error."""


class PstrykBleBoxClient:
    """Client for local BleBox meter API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
    ) -> None:
        """Initialize the BleBox client."""
        self._session = session
        self._host = host

    async def get_state(self) -> dict[str, Any]:
        """Fetch meter state from local API."""
        url = f"http://{self._host}/state"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise PstrykBleBoxError(
                f"Cannot connect to BleBox meter at {self._host}: {err}"
            ) from err

    async def validate_connection(self) -> bool:
        """Validate connection to BleBox meter."""
        try:
            data = await self.get_state()
            return "multiSensor" in data
        except PstrykBleBoxError:
            return False

    @staticmethod
    def parse_sensors(raw: dict[str, Any]) -> dict[int, dict[str, float]]:
        """Parse multiSensor response into phase-indexed dict with scaled values."""
        sensors = raw.get("multiSensor", {}).get("sensors", [])
        phases: dict[int, dict[str, float]] = {}
        for sensor in sensors:
            phase_id = sensor.get("id")
            sensor_type = sensor.get("type")
            value = sensor.get("value")
            if phase_id is None or sensor_type is None or value is None:
                continue
            scale = BLEBOX_SCALE.get(sensor_type, 1)
            phases.setdefault(phase_id, {})[sensor_type] = value / scale
        return phases
