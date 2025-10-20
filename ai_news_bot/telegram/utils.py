import re


def chunk_message(message: str, chunk_size: int = 4000) -> list[str]:
    """Split a message into chunks of a specified size."""
    return [
        message[i:i + chunk_size]
        for i in range(0, len(message), chunk_size)
    ]


def clear_html_tags(text: str) -> str:
    """Remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)