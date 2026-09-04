from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# Alembic 迁移会用这些命名规则生成约束名，避免不同环境生成的名字不一致。
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # 所有 models/*.py 的表模型都继承 Base，SQLAlchemy 才知道这些类对应数据库表。
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# engine 是数据库连接引擎，settings.database_url 来自 .env 中的 MySQL 配置。
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    # pool_pre_ping 会在使用连接前探活，减少 MySQL 断开空闲连接导致的报错。
    pool_pre_ping=True,
    pool_recycle=3600,
)

# SessionLocal 是“数据库会话工厂”；每个请求通过 get_db 创建一个 Session，用完关闭。
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
