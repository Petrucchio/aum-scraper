import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_companies_empty(client: AsyncClient):
    """Test listing companies when database is empty"""
    response = await client.get("/api/v1/companies/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_companies_with_data(client: AsyncClient, sample_company):
    """Test listing companies with data"""
    response = await client.get("/api/v1/companies/")
    assert response.status_code == 200
    
    companies = response.json()
    assert len(companies) == 1
    assert companies[0]["name"] == "Empresa Teste"
    assert companies[0]["url_site"] == "https://empresateste.com.br"

@pytest.mark.asyncio
async def test_get_company_by_id(client: AsyncClient, sample_company):
    """Test getting a specific company by ID"""
    response = await client.get(f"/api/v1/companies/{sample_company.id}")
    assert response.status_code == 200
    
    company = response.json()
    assert company["name"] == "Empresa Teste"
    assert company["id"] == sample_company.id

@pytest.mark.asyncio
async def test_get_company_not_found(client: AsyncClient):
    """Test getting a non-existent company"""
    response = await client.get("/api/v1/companies/999")
    assert response.status_code == 404
    assert "não encontrada" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_company_latest_aum(client: AsyncClient, sample_aum_snapshot):
    """Test getting latest AUM for a company"""
    company_id = sample_aum_snapshot.company_id
    
    response = await client.get(f"/api/v1/companies/{company_id}/latest-aum")
    assert response.status_code == 200
    
    data = response.json()
    assert data["company_id"] == company_id
    assert data["aum_raw_text"] == "R$ 2,5 bi"
    assert data["aum_normalized"] == 2.5e9

@pytest.mark.asyncio
async def test_get_companies_summary(client: AsyncClient, sample_aum_snapshot):
    """Test getting companies summary statistics"""
    response = await client.get("/api/v1/companies/stats/summary")
    assert response.status_code == 200
    
    summary = response.json()
    assert summary["total_companies"] == 1
    assert summary["companies_with_aum"] == 1
    assert summary["success_rate"] == 1.0
    assert summary["total_aum"] == 2.5e9