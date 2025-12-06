from datetime import datetime, timedelta

from app.services.inventory_service import (
    SaleRecord,
    analyze_inventory_dashboard,
    get_inventory_movements,
)


def _sample_sales(base: datetime):
    return [
        SaleRecord(product="ProdA", amount=100.0, channel="web", date=base),
        SaleRecord(product="ProdA", amount=120.0, channel="store", date=base + timedelta(days=1)),
        SaleRecord(product="ProdB", amount=55.0, channel="web", date=base + timedelta(days=2)),
    ]


def test_inventory_dashboard_raises_alerts_with_low_stock():
    base = datetime(2025, 5, 1)
    sales = _sample_sales(base)

    dashboard = analyze_inventory_dashboard(
        "tenant-x",
        start=base,
        end=base + timedelta(days=3),
        safety_days=5,
        stock_by_product={"ProdA": 4, "ProdB": 20},
        sales_data=sales,
    )

    assert dashboard["summary"]["alerts"] >= 1
    assert any(p["product"] == "ProdA" and p["reorder_alert"] for p in dashboard["products"])


def test_inventory_movements_timeline():
    base = datetime.now() - timedelta(days=2)
    sales = _sample_sales(base)

    movements = get_inventory_movements(
        "tenant-y",
        days=10,
        product=None,
        channel=None,
        sales_data=sales,
    )

    assert len(movements) == 3
    assert movements[0]["units"] == 1
