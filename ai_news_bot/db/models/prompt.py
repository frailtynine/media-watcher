from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import JSON, Text

from ai_news_bot.ai.prompts import Prompts
from ai_news_bot.db.base import Base


class Prompt(Base):
    __tablename__ = "prompt"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(
        Text(3000),
        nullable=False,
        default=Prompts.ROLE,
    )
    crypto_role: Mapped[str] = mapped_column(
        Text(3000),
        nullable=False,
        default=Prompts.ROLE_CRYPTO,
    )
    suggest_post: Mapped[str] = mapped_column(
        Text(3000),
        nullable=False,
        default=Prompts.SUGGEST_POST,
    )
    post_examples: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=[
            Prompts.POST_EXAMPLE_ONE,
            Prompts.POST_EXAMPLE_TWO,
        ],
    )
