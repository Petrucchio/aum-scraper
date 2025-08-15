import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.company import Company
from app.models.aum_snapshot import AUMSnapshot
from app.models.scrape_log import ScrapeLog
from app.models.usage import Usage

# Banco de dados de teste
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine):
    """Create test database session"""
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def client(test_db):
    """Create test client with test database"""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def sample_company(test_db):
    """Create a sample company for testing"""
    company = Company(
        name="Empresa Teste",
        url_site="https://empresateste.com.br",
        url_linkedin="https://linkedin.com/company/empresateste",
        url_instagram="https://instagram.com/empresateste",
        url_x="https://x.com/empresateste"
    )
    
    test_db.add(company)
    await test_db.commit()
    await test_db.refresh(company)
    
    return company

@pytest.fixture
async def sample_aum_snapshot(test_db, sample_company):
    """Create a sample AUM snapshot for testing"""
    aum_snapshot = AUMSnapshot(
        company_id=sample_company.id,
        aum_raw_text="R$ 2,5 bi",
        aum_normalized=2.5e9,
        source_url="https://empresateste.com.br",
        source_content="Empresa teste com patrimônio sob gestão de R$ 2,5 bilhões",
        extraction_method="gpt4o",
        confidence_score=0.9
    )
    
    test_db.add(aum_snapshot)
    await test_db.commit()
    await test_db.refresh(aum_snapshot)
    
    return aum_snapshot