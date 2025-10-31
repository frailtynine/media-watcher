import httpx

from ai_news_bot.ai.telegram_producer import fetch_rss_feed


async def validate_rss_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that the provided URL is a valid RSS feed.

    Args:
        url: The RSS feed URL to validate.

    Returns:
        A tuple containing a boolean indicating whether the URL 
        is valid and the validated RSS feed URL or None.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            return False, "RSS недоступен по указанному URL."
        content_type = response.headers.get("Content-Type", "")
        if "xml" not in content_type:
            return False, "Кажется, это не RSS-лента."
        return True, url


# TODO: rework so it doesn't create abominations like
# https://t.me/https://example.com/some_channel
async def validate_telegram_channel_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that the provided URL is a valid Telegram channel RSS feed.

    Args:
        url: The Telegram channel URL to validate.

    Returns:
        A tuple containing a boolean indicating whether the URL is valid
        and the validated Telegram channel URL or None.
    """
    if not url.startswith("https://t.me/"):
        url = "https://t.me/" + url.lstrip("/").lstrip("t.me/").lstrip("@")
    try:
        response = await fetch_rss_feed(url)
    except httpx.TimeoutException:
        return False, "Что-то пошло не так. Попробуйте еще."
    except Exception as e:
        return False, f"Произошла ошибка при проверке канала: {e}"
    if not response:
        return False, "Telegram-канал недоступен или URL неверен."
    return True, url
