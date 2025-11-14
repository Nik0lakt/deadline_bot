from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

def build_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)
