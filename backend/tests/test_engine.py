import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from app.services.engine import PredictionEngine


# --- FIXTURES ---

@pytest.fixture
def mock_finviz_html():
    """
    Returns a fake HTML string simulating a successful Finviz response.
    We create a table with 3 stocks:
    - NVDA: +5.0% (Gainer)
    - AAPL: -2.5% (Loser)
    - MSFT: +1.0% (Middle)
    """
    return """
    <div id="screener-content">
        <table>
            <tr class="table-dark-row-cp">
                <td>1</td>
                <td>NVDA</td> <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>150.00</td> <td>5.00%</td>  <td>20M</td>    </tr>

            <tr class="table-light-row-cp">
                <td>2</td>
                <td>AAPL</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>180.00</td>
                <td>-2.50%</td>
                <td>15M</td>
            </tr>

            <tr class="table-dark-row-cp">
                <td>3</td>
                <td>MSFT</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>...</td>
                <td>400.00</td>
                <td>1.00%</td>
                <td>10M</td>
            </tr>
        </table>
    </div>
    """


@pytest.fixture
def mock_yf_data():
    """
    Returns a fake Pandas DataFrame simulating yf.download response.
    """
    data = {
        "NVDA": [140.0, 150.0],  # 140 -> 150 = +7.1%
        "AAPL": [185.0, 180.0],  # 185 -> 180 = -2.7%
        "MSFT": [395.0, 400.0]  # 395 -> 400 = +1.2%
    }
    df = pd.DataFrame(data, index=["2024-01-01", "2024-01-02"])
    return df


# --- TESTS ---

def test_market_movers_finviz_success(mock_finviz_html):
    """
    Test that the engine prefers Finviz data when available.
    """
    engine = PredictionEngine()

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_finviz_html.encode("utf-8")
        mock_get.return_value = mock_resp

        with patch("yfinance.download") as mock_yf:
            # ACT
            result = engine.get_market_movers()

            # ASSERT
            assert len(result.gainers) > 0
            assert len(result.losers) > 0

            # NVDA should be the top gainer (+5.00%)
            assert result.gainers[0].symbol == "NVDA"
            assert result.gainers[0].change_pct == 5.0

            # AAPL should be the top loser (-2.50%)
            assert result.losers[0].symbol == "AAPL"
            assert result.losers[0].change_pct == -2.5

            # Efficiency Check: YFinance should NOT be called
            mock_yf.assert_not_called()


def test_market_movers_fallback_to_yf(mock_yf_data):
    """
    Test that the engine correctly switches to YFinance if Finviz fails.
    """
    engine = PredictionEngine()

    # 1. Force Finviz to Fail
    with patch("requests.get", side_effect=Exception("Connection Refused")):
        # 2. Mock yfinance to return a DICT containing our DataFrame.
        # This allows yf.download(...)['Close'] to work naturally.
        with patch("yfinance.download", return_value={"Close": mock_yf_data}):
            # ACT
            result = engine.get_market_movers()

            # ASSERT
            # Gainers: NVDA (+7.1%) and MSFT (+1.2%)
            assert len(result.gainers) >= 1
            assert result.gainers[0].symbol == "NVDA"
            assert result.gainers[0].change_pct > 0

            # Losers: AAPL (-2.7%)
            assert len(result.losers) >= 1
            assert result.losers[0].symbol == "AAPL"
            assert result.losers[0].change_pct < 0


def test_market_movers_total_failure():
    """
    Test that the engine handles total failure gracefully (empty lists).
    """
    engine = PredictionEngine()

    with patch("requests.get", side_effect=Exception("Finviz Down")):
        with patch("yfinance.download", side_effect=Exception("YF Down")):
            result = engine.get_market_movers()

            assert result.gainers == []
            assert result.losers == []
            assert result.active == []