import re

from ai_news_bot.web.api.news_task.schema import RSSItemSchema


def parse_rsss_item(query) -> RSSItemSchema | None:
    """
    Parse the RSS item from the callback query message.

    :param query: CallbackQuery object containing the message text.
    :return: RSSItemSchema with parsed details.
    """
    message = query.message
    message_text = message.text if message and message.text else None
    news_details = {}
    if not message_text:
        return None
    title_match = re.search(r"News: (.*?)(?:\n|$)", message_text)
    if title_match:
        news_details["title"] = title_match.group(1).strip()
    link_match = re.search(r"Link: (https?://\S+)(?:\n|$)", message_text)
    if link_match:
        news_details["link"] = link_match.group(1).strip()
    desc_match = re.search(r"Description: (.*?)(?:\n|$)", message_text)
    if desc_match:
        news_details["description"] = desc_match.group(1).strip()
    news_details["pub_date"] = message.date

    try:
        return RSSItemSchema(**news_details) if news_details else None
    except (ValueError, TypeError):
        return None
