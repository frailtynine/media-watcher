# from typing import List

# from fastapi import APIRouter
# from fastapi.param_functions import Depends
# from sqlalchemy.ext.asyncio import AsyncSession

# from ai_news_bot.db.crud.base import BaseCRUD
# from ai_news_bot.db.dao.dummy_dao import DummyDAO
# from ai_news_bot.db.dependencies import get_db_session
# from ai_news_bot.db.models.dummy_model import DummyModel
# from ai_news_bot.web.api.dummy.schema import DummyModelDTO, DummyModelInputDTO

# router = APIRouter()


# @router.get("/", response_model=List[DummyModelDTO])
# async def get_dummy_models(
#     limit: int = 10,
#     offset: int = 0,
#     dummy_dao: DummyDAO = Depends(),
# ) -> List[DummyModel]:
#     """
#     Retrieve all dummy objects from the database.

#     :param limit: limit of dummy objects, defaults to 10.
#     :param offset: offset of dummy objects, defaults to 0.
#     :param dummy_dao: DAO for dummy models.
#     :return: list of dummy objects from database.
#     """
#     return await dummy_dao.get_all_dummies(limit=limit, offset=offset)


# @router.get("/{dummy_id}", response_model=DummyModelDTO)
# async def get_dummy_model(
#     dummy_id: int,
#     session: AsyncSession = Depends(get_db_session),
# ):
#     """
#     Retrieve dummy object by ID.

#     :param dummy_id: ID of the dummy object.
#     :param session: database session.
#     :return: dummy object from database.
#     """
#     crud = BaseCRUD(DummyModel)
#     return await crud.get_object_by_id(session=session, obj_id=dummy_id)


# @router.put("/")
# async def create_dummy_model(
#     new_dummy_object: DummyModelInputDTO,
#     session: AsyncSession = Depends(get_db_session),
# ) -> None:
#     """
#     Creates dummy model in the database.

#     :param new_dummy_object: new dummy model item.
#     :param dummy_dao: DAO for dummy models.
#     """
#     crud = BaseCRUD(DummyModel)
#     await crud.create(
#         session=session,
#         obj_in=new_dummy_object,
#     )
