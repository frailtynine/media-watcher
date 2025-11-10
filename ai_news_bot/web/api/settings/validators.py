import httpx

from ai_news_bot.ai.telegram_producer import fetch_rss_feed


def normalize_telegram_url(url: str) -> str:
    """
    Normalize a Telegram channel URL to the standard https://t.me/ format.
    
    Handles various input formats:
    - @channelname -> https://t.me/channelname
    - t.me/channelname -> https://t.me/channelname
    - channelname -> https://t.me/channelname
    - https://t.me/channelname -> https://t.me/channelname (unchanged)
    
    Args:
        url: The Telegram channel URL or username to normalize.
        
    Returns:
        A properly formatted Telegram URL starting with https://t.me/
    """
    if url.startswith("https://t.me/"):
        return url
        
    # Remove common prefixes properly to avoid cutting channel names
    if url.startswith("t.me/"):
        url = url[5:]  # Remove "t.me/"
    elif url.startswith("@"):
        url = url[1:]  # Remove "@"
    
    # Remove leading slashes
    url = url.lstrip("/")
    
    # Add proper prefix
    return "https://t.me/" + url


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


async def validate_telegram_channel_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that the provided URL is a valid Telegram channel RSS feed.

    Args:
        url: The Telegram channel URL to validate.

    Returns:
        A tuple containing a boolean indicating whether the URL is valid
        and the validated Telegram channel URL or None.
    """
    normalized_url = normalize_telegram_url(url)
    
    try:
        response = await fetch_rss_feed(normalized_url)
    except httpx.TimeoutException:
        return False, "Что-то пошло не так. Попробуйте еще."
    except Exception as e:
        return False, f"Произошла ошибка при проверке канала: {e}"
    if not response:
        return False, "Telegram-канал недоступен или URL неверен."
    return True, normalized_url
