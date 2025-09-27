from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.prompt import Prompt
from ai_news_bot.ai.prompts import Prompts


class CRUDPrompt(BaseCRUD):
    async def add_post_example(
        self,
        session: AsyncSession,
        example: str,
    ) -> Prompt:
        """Add a new post example to the prompt."""
        prompt = await self.get_all_objects(session)
        prompt = prompt[0] if prompt else None
        if not prompt:
            raise ValueError("No prompt found in the database.")
        examples = prompt.post_examples
        if example not in examples:
            examples.append(example)
            prompt.post_examples = examples
            flag_modified(prompt, "post_examples")
            session.add(prompt)
            await session.flush()
            await session.refresh(prompt)
            return prompt
        else:
            raise ValueError("Example already exists.")

    async def remove_post_example(
        self,
        session: AsyncSession,
        example: str,
    ) -> Prompt:
        """Remove a post example from the prompt."""
        prompt = await self.get_all_objects(session)
        prompt = prompt[0] if prompt else None
        if not prompt:
            raise ValueError("No prompt found in the database.")
        examples: list[str] = prompt.post_examples
        if example in examples:
            examples.remove(example)
            prompt.post_examples = examples
            flag_modified(prompt, "post_examples")
            session.add(prompt)
            await session.flush()
            await session.refresh(prompt)
            return prompt
        else:
            raise ValueError("Example not found.")

    async def create(
        self,
        session: AsyncSession,
    ) -> Prompt:
        """Create a new prompt configuration."""
        existing_prompts = await self.get_all_objects(session)
        if existing_prompts:
            raise ValueError("Prompt configuration already exists.")
        prompt = self.model()
        session.add(prompt)
        await session.flush()
        await session.refresh(prompt)
        return prompt

    async def get_or_create(
        self,
        session: AsyncSession,
    ) -> Prompt:
        """Get the existing prompt configuration or create a new one."""
        existing_prompts = await self.get_all_objects(session)
        if existing_prompts:
            return existing_prompts[0]
        return await self.create(session=session)

    async def reset_to_default(
        self,
        session: AsyncSession,
    ) -> Prompt:
        """Reset the prompt configuration to default values."""
        prompt = await self.get_or_create(session=session)
        prompt.role = Prompts.ROLE
        prompt.crypto_role = Prompts.ROLE_CRYPTO
        prompt.suggest_post = Prompts.SUGGEST_POST
        prompt.post_examples = [
            Prompts.POST_EXAMPLE_ONE,
            Prompts.POST_EXAMPLE_TWO,
        ]
        flag_modified(prompt, "post_examples")
        session.add(prompt)
        await session.flush()
        await session.refresh(prompt)
        return prompt


crud_prompt = CRUDPrompt(Prompt)
