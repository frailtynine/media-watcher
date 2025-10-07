def chunk_message(message: str, chunk_size: int = 4000) -> list[str]:
    """Split a message into chunks of a specified size."""
    return [
        message[i:i + chunk_size]
        for i in range(0, len(message), chunk_size)
    ]
