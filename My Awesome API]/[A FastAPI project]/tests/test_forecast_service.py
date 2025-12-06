from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.models import Sale, Tenant
from app.services.forecast_service import get_forecast_data


def _get_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_forecast_includes_metadata_and_trend():
    db = _get_session()
    tenant = Tenant(name="Tenant Forecast", code="t-fc")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    base_date = datetime(2025, 1, 1)
    sales = []
    for i in range(15):
        sales.append(
            Sale(
                tenant_id=tenant.id,
                amount=100 + i * 10,  # upward trend
                product="A",
                channel="web",
                date=base_date + timedelta(days=i),
            )
        )
    db.add_all(sales)
    db.commit()

    result = get_forecast_data("t-fc", "2025-02-01", "2025-02-03", db=db)

    assert result.forecast
    assert len(result.forecast) == 3
    assert result.meta is not None
    assert result.meta.trend == "up"
    assert 0 <= result.meta.confidence <= 1
    assert result.products is not None

