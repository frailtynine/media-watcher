from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.settings import Settings


class SettingsCRUD(BaseCRUD):
    async def add_source_to_dict(
        self,
        session: AsyncSession,
        source_name: str,
        url: str,
        field_name: str,
    ) -> Settings:
        """Add or update an item in the settings dictionary.

        Args:
            session (AsyncSession): Database session.
            key (str): Key to add or update.
            value (str): Value to associate with the key.
            field_name (str): The name of the dictionary field to update.
                Must be either 'rss_urls' or 'tg_urls'.
        """
        if field_name not in {"rss_urls", "tg_urls"}:
            raise ValueError("Invalid field name")
        settings = await self.get_all_objects(session=session)
        settings = settings[0] if settings else None
        if settings is None:
            raise ValueError("Settings not found")
        current_dict = getattr(settings, field_name, {})
        current_dict[source_name] = url
        setattr(settings, field_name, current_dict)
        flag_modified(settings, field_name)
        session.add(settings)
        await session.flush()
        await session.refresh(settings)
        return settings
    
    async def remove_source_from_dict(
        self,
        session: AsyncSession,
        source_name: str,
        field_name: str,
    ) -> Settings:
        """Remove an item from the settings dictionary.

        Args:
            session (AsyncSession): Database session.
            key (str): Key to remove.
            field_name (str): The name of the dictionary field to update.
                Must be either 'rss_urls' or 'tg_urls'.
        """
        if field_name not in {"rss_urls", "tg_urls"}:
            raise ValueError("Invalid field name")
        settings = await self.get_all_objects(session=session)
        settings = settings[0] if settings else None
        if settings is None:
            raise ValueError("Settings not found")
        current_dict = getattr(settings, field_name, {})
        if source_name in current_dict:
            del current_dict[source_name]
            setattr(settings, field_name, current_dict)
            flag_modified(settings, field_name)
            session.add(settings)
            await session.flush()
            await session.refresh(settings)
        return settings


settings_crud = SettingsCRUD(Settings)
