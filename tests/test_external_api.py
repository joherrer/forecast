import os

import pytest

from app.data import spots
from app.helpers import get_forecast_info


@pytest.mark.external
@pytest.mark.skipif(
    os.getenv("RUN_EXTERNAL_API_TESTS") != "1",
    reason="Set RUN_EXTERNAL_API_TESTS=1 to call the Surfline API.",
)
def test_surfline_api_wave_forecast_returns_data():
    # Opt-in smoke check for the third-party integration; keep it out of the default suite.
    spot_id = spots["Kirra"]["id"]

    response = get_forecast_info("wave", spot_id)

    assert response is not None
    assert "data" in response
    assert "wave" in response["data"]
    assert isinstance(response["data"]["wave"], list)
