from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


DATABASE_URL = "postgresql://admin:password@localhost/data_db"
DATABASE_URL_ASYNC = "postgresql+asyncpg://postgres:password@db:5432/data_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True)
async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()


class ArrayModel(BaseModel):
    array: List[Optional[str]]


@app.post("/sum")
def sum_numbers(data: ArrayModel):
    """
    Суммирует числа, переданные в теле запроса

    Этот метод обрабатывает POST-запрос на URL "/sum". Он ожидает, что в теле запроса будет передан JSON-объект,
    содержащий массив чисел в виде строк. Любые нечисловые значения будут проигнорированы

    Args:
    - data (ArrayModel): Данные, переданные в теле запроса

    Returns:
    - dict: Словарь с ключом "sum" и значением, равным сумме чисел в массиве
    """
    numbers = []
    for num in data.array:
        if num is not None:
            try:
                number = int(num)
                numbers.append(number)
            except ValueError:
                pass
    return {"sum": sum(numbers)}


async def get_db():
    """
    Асинхронный генератор для создания сессии бд

    Этот генератор используется в качестве зависимости в FastAPI для предоставления сессии бд в каждом запросе,
    который ее требует. Он создает асинхронную сессию бд с помощью `async_session_maker` и возвращает ее через `yield`

    Yields:
        AsyncSession: Асинхронная сессия бд
    """
    async with async_session_maker() as session:
        yield session


@app.post("/sum_async")
async def sum_numbers_async(data: ArrayModel, db: AsyncSession = Depends(get_db)):
    """
    Асинхронно суммирует числа, переданные в теле запроса, и сохраняет результат в базе данных

    Этот метод обрабатывает POST-запрос на URL "/sum_async". Он ожидает, что в теле запроса будет передан JSON-объект,
    содержащий массив чисел в виде строк. Любые нечисловые значения будут проигнорированы

    Args:
    - data (ArrayModel): Данные, переданные в теле запроса
    - db (AsyncSession): Асинхронная сессия базы данных, предоставленная зависимостью

    Returns:
    - dict: Словарь с ключами "session_id" и "result"
    """
    numbers = []
    for num in data.array:
        if num is not None:
            try:
                number = int(num)
                numbers.append(number)
            except ValueError:
                pass

    result = sum(numbers)
    new_session = Session(result=result, status="COMPLETED")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return {"session_id": new_session.id, "result": result}