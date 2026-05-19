import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# SSL 설정 (RDS 연결용, 인증서 파일이 있을 때만 적용)
_cert_path = "/app/global-bundle.pem"
if os.path.exists(_cert_path):
    ssl_ctx = ssl.create_default_context(cafile=_cert_path)
    connect_args = {"ssl": ssl_ctx}
else:
    connect_args = {}

# 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args=connect_args
)

# 세션 팩토리
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# DB 세션 의존성 주입
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise