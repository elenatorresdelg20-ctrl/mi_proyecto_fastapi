from io import BytesIO
from typing import Any, Dict, List


def _col_letter(idx: int) -> str:
    result = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def _make_cell(row: int, col: int, value: Any, formula: str | None = None):
    ref = f"{_col_letter(col)}{row}"
    if formula:
        return f'<c r="{ref}"><f>{formula}</f><v>{value if isinstance(value, (int, float)) else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'


def _build_sheet_xml(rows: List[List[Any]], formulas: Dict[str, str] | None = None) -> str:
    xml_rows: List[str] = []
    formulas = formulas or {}
    for r_idx, row in enumerate(rows, start=1):
        cells: List[str] = []
        for c_idx, val in enumerate(row, start=1):
            ref = f"{_col_letter(c_idx)}{r_idx}"
            cells.append(_make_cell(r_idx, c_idx, val, formulas.get(ref)))
        xml_rows.append(f"<row r=\"{r_idx}\">{''.join(cells)}</row>")
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        f"<sheetData>{''.join(xml_rows)}</sheetData>"
        "</worksheet>"
    )


def _build_workbook_xml(sheet_names: List[str]) -> str:
    sheets_xml = []
    for idx, name in enumerate(sheet_names, start=1):
        sheets_xml.append(f'<sheet name="{name}" sheetId="{idx}" r:id="rId{idx}"/>')
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        f"<sheets>{''.join(sheets_xml)}</sheets>"
        "</workbook>"
    )


def _build_workbook_rels(sheet_names: List[str]) -> str:
    rels = []
    for idx, _ in enumerate(sheet_names, start=1):
        rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{idx}.xml"/>'
        )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        f"{''.join(rels)}"
        "</Relationships>"
    )


def _build_content_types(sheet_count: int) -> str:
    overrides = []
    for idx in range(1, sheet_count + 1):
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f"{''.join(overrides)}"
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )


def _build_styles_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<fonts count=\"1\"><font><sz val=\"11\"/><color theme=\"1\"/><name val=\"Calibri\"/></font></fonts>"
        "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
        "<borders count=\"1\"><border/></borders>"
        "<cellStyleXfs count=\"1\"><xf/></cellStyleXfs>"
        "<cellXfs count=\"1\"><xf xfId=\"0\"/></cellXfs>"
        "</styleSheet>"
    )


def _package_excel(sheets: Dict[str, str]) -> BytesIO:
    import zipfile

    sheet_names = list(sheets.keys())
    mem = BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _build_content_types(len(sheet_names)))
        zf.writestr("_rels/.rels", """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='xl/workbook.xml'/>
</Relationships>""")
        zf.writestr("xl/workbook.xml", _build_workbook_xml(sheet_names))
        zf.writestr("xl/_rels/workbook.xml.rels", _build_workbook_rels(sheet_names))
        zf.writestr("xl/styles.xml", _build_styles_xml())
        for idx, (name, content) in enumerate(sheets.items(), start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", content)
    mem.seek(0)
    return mem


def generate_pptx_report(tenant_code: str, payload):
    """PPTX placeholder: mantiene compatibilidad devolviendo bytes válidos."""
    return BytesIO(b"PPTX content coming from professional SaaS builder")


def _build_kpi_sheet(payload: Dict[str, Any]) -> str:
    kpis = payload.get("kpis", payload) if isinstance(payload, dict) else {}
    rows = [
        ["Métrica", "Valor"],
        ["Ventas", kpis.get("ventas", 0)],
        ["Transacciones", kpis.get("transacciones", 0)],
        ["Ticket promedio", kpis.get("ticket_promedio", 0)],
        ["Margen", kpis.get("margen", 0)],
    ]
    formulas = {"B6": "IF(B2=0,0,B5/B2)"}
    rows.append(["Margen %", ""])
    return _build_sheet_xml(rows, formulas=formulas)


def _build_inventory_sheet(payload: Dict[str, Any]) -> str:
    inventory = payload.get("inventory", {}) if isinstance(payload, dict) else {}
    products = inventory.get("products", [])
    rows: List[List[Any]] = [
        ["Producto", "Stock", "Cobertura (días)", "Reorden", "Alerta", "Ticket prom.", "Ingresos"],
    ]
    for product in products:
        rows.append(
            [
                product.get("product"),
                product.get("stock_units", 0),
                product.get("coverage_days", 0),
                product.get("reorder_point", 0),
                "SI" if product.get("reorder_alert") else "NO",
                product.get("avg_ticket", 0),
                product.get("revenue", 0),
            ]
        )
    if len(rows) == 1:
        rows.append(["Sin datos", 0, 0, 0, "NO", 0, 0])
    return _build_sheet_xml(rows)


def _build_movements_sheet(payload: Dict[str, Any]) -> str:
    inventory = payload.get("inventory", {}) if isinstance(payload, dict) else {}
    movements = inventory.get("movements", [])
    rows: List[List[Any]] = [["Fecha", "Unidades", "Ingresos"]]
    for mv in movements:
        rows.append([mv.get("date"), mv.get("units", 0), mv.get("revenue", 0)])
    if len(rows) == 1:
        rows.append(["N/A", 0, 0])
    return _build_sheet_xml(rows)


def _build_dashboard_sheet() -> str:
    rows = [
        ["Indicador", "Valor"],
        ["Inventario total", "=SUM(Inventario!B2:B200)"],
        ["Alerta de reorden", "=COUNTIF(Inventario!E2:E200,\"SI\")"],
        ["Unidades últimas 7d", "=SUM(Movimientos!B2:B8)"],
        ["Ingresos últimos 7d", "=SUM(Movimientos!C2:C8)"],
    ]
    return _build_sheet_xml(rows)


def generate_excel_report(tenant_code: str, payload: Dict[str, Any]):
    """Genera un Excel con hojas de KPIs, inventario, movimientos y dashboard calculado."""

    sheets = {
        "Resumen KPI": _build_kpi_sheet(payload),
        "Inventario": _build_inventory_sheet(payload),
        "Movimientos": _build_movements_sheet(payload),
        "Dashboard": _build_dashboard_sheet(),
    }

    return _package_excel(sheets)


def generate_calculated_excel_report(tenant_code: str, payload: Dict[str, Any]):
    """Genera un Excel con fórmulas adicionales y totales cruzados para BI ligero."""

    sheets = {
        "Resumen KPI": _build_kpi_sheet(payload),
        "Inventario": _build_inventory_sheet(payload),
        "Movimientos": _build_movements_sheet(payload),
        "Dashboard": _build_dashboard_sheet(),
        "Calculado": _build_sheet_xml(
            [
                ["KPIs + Inventario", ""],
                ["Margen %", "=IF('Resumen KPI'!B2=0,0,'Resumen KPI'!B5/'Resumen KPI'!B2)"],
                ["Cobertura media", "=AVERAGE(Inventario!C2:C200)"],
                ["Reordenes críticos", "=COUNTIF(Inventario!E2:E200,\"SI\")"],
                ["Ingresos totales", "=SUM(Movimientos!C2:C200)"],
            ]
        ),
    }
    return _package_excel(sheets)
