import zipfile

from app.services.report_service import (
    generate_calculated_excel_report,
    generate_excel_report,
    generate_pptx_report,
)


def _payload():
    return {
        "kpis": {"ventas": 1000, "transacciones": 10, "ticket_promedio": 100, "margen": 400},
        "inventory": {
            "products": [
                {
                    "product": "ProdA",
                    "stock_units": 12,
                    "coverage_days": 6,
                    "reorder_point": 5,
                    "reorder_alert": False,
                    "avg_ticket": 80,
                    "revenue": 500,
                }
            ],
            "movements": [{"date": "2025-05-01", "units": 3, "revenue": 240.0}],
        },
        "forecast": [
            {"date": "2025-05-02", "expected_amount": 300.0},
        ],
        "meta": {"trend": "up", "confidence": 0.92},
    }


def test_excel_report_contains_dashboard_sheet():
    excel = generate_excel_report("t1", _payload())

    with zipfile.ZipFile(excel) as zf:
        assert "xl/worksheets/sheet4.xml" in zf.namelist()
        dashboard_xml = zf.read("xl/worksheets/sheet4.xml").decode()
        assert "Dashboard" not in dashboard_xml  # sheet name stored in workbook, but formulas exist
        assert "SUM(Movimientos!B2:B8)" in dashboard_xml


def test_calculated_excel_has_formulas():
    excel = generate_calculated_excel_report("t1", _payload())

    with zipfile.ZipFile(excel) as zf:
        calc_sheet = zf.read("xl/worksheets/sheet5.xml").decode()
        assert "COUNTIF(Inventario!E2:E200" in calc_sheet
        assert "SUM(Movimientos!C2:C200" in calc_sheet


def test_pptx_contains_dynamic_bullets():
    ppt = generate_pptx_report("tenant-x", _payload())

    with zipfile.ZipFile(ppt) as zf:
        assert "ppt/slides/slide1.xml" in zf.namelist()
        assert "ppt/slides/slide2.xml" in zf.namelist()

        slide1 = zf.read("ppt/slides/slide1.xml").decode()
        slide2 = zf.read("ppt/slides/slide2.xml").decode()

        assert "Reporte tenant-x" in slide1
        assert "Ventas: 1000" in slide1
        assert "Inventario & Forecast" in slide2
        assert "Tendencia: up" in slide2
