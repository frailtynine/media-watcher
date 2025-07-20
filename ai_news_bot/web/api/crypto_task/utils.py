import httpx

from ai_news_bot.settings import settings

URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"


async def get_crypto_price(ticker: str) -> float:
    """Get the current price of a cryptocurrency by its ticker."""
    api_key = settings.coinmarketcap_api_key
    if not api_key:
        raise ValueError("CoinMarketCap API key is not set in settings.")
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }
    params = {"slug": ticker, "convert": "USD"}
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers, params=params)
        data = response.json()
        crypto_id = next(iter(data["data"]))
        return data["data"][crypto_id]["quote"]["USD"]["price"]
