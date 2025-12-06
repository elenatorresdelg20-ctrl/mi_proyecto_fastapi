from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.models import Sale, Tenant
from app.services.kpi_service import calculate_kpis


def _get_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_calculate_kpis_in_range():
    db = _get_session()
    tenant = Tenant(name="Tenant KPI", code="t1")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    base_date = datetime(2025, 1, 15)
    db.add_all(
        [
            Sale(tenant_id=tenant.id, amount=100.0, product="A", channel="web", date=base_date),
            Sale(tenant_id=tenant.id, amount=200.0, product="B", channel="store", date=base_date + timedelta(days=1)),
            # fuera de rango, no debe contarse
            Sale(tenant_id=tenant.id, amount=50.0, product="C", channel="store", date=base_date - timedelta(days=60)),
        ]
    )
    db.commit()

    kpis = calculate_kpis("t1", start=date(2025, 1, 1), end=date(2025, 1, 31), cost_ratio=0.5, db=db)

    assert kpis is not None
    assert kpis.ventas == 300.0
    assert kpis.transacciones == 2
    assert kpis.ticket_promedio == 150.0
    # margen = ventas - costo (50% de 300)
    assert kpis.margen == 150.0


def test_calculate_kpis_invalid_range():
    db = _get_session()
    tenant = Tenant(name="Tenant KPI", code="t2")
    db.add(tenant)
    db.commit()

    with pytest.raises(ValueError):
        calculate_kpis("t2", start=date(2025, 2, 1), end=date(2025, 1, 1), db=db)
