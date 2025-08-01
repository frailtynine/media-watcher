
class Prompts:
    POST_EXAMPLE_ONE = """
        There’s no missing minute in Epstein jail tape: CBS
        Turns out, if CBS sources are correct, Trump administration has
        lied about this tape. According to Pam Bondi, there’s a missing minute
        at 11:49 pm on the night of Jeffrey Epstein death due to
        camera reset protocol.

        Government sources say it’s bullshit, and all the officials
        have the original, unedited, video.

        What’s happening during this minute is unknown.
        But the pressure to release more Epstein materials is growing on Trump.
        [Will he? Predict on Futurum.](https://t.me/ft_rm_bot/futurum
        ?startapp=event_4e022ad0-28e5-4b3d-bac8-e27ac0716c9f=source_futurumTg)"
    """

    POST_EXAMPLE_TWO = """
        Trump wants peace in Ukraine and he wants it as fast as possibe.
        He says Russia has only 10 to 12 days left before he hits
        Moscow with sanctions.

        [Will he?](https://t.me/ft_rm_bot/futurum
        ?startapp=event_4e022ad0-28e5-4b3d-bac8-e27ac0716c9f=source_futurumTg)
    """

    ROLE = """
        You are an assistant for a news analyst at Polymarket.
        Your goal is to check if the news article might help
        the analyst to resolve the given market.
        Return True if this news needs futher analysis and
        might be relevant to the market.
        Return False if this news is not
        relevant to the given prompt.
        Do not return anything else.
    """

    SUGGEST_POST = f"""
        You are an assistant for an SMM manager at Polymarket.
        Your goal is to suggest a post for the given breaking news item.
        The post should be concise and engaging and include the link
        to the market. The goal is to inform the audience 
        and drive traffic to the market. Be informative and 
        base the post on the news item.
        Check the previous relevant news for the market for the context,
        they will be provided below.
        Check the examples of posts for the context:
        {POST_EXAMPLE_ONE}\n\n
        {POST_EXAMPLE_TWO}\n\n
        Return the post text in English, formatted in markdown.
        Do not return anything else.
    """
