import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def _clean_header(name: str) -> str:
    name = str(name or "").strip().lower()
    name = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_clean_header(c) for c in df.columns]
    return df


def detect_column_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    keywords = {
        "date": ["fecha", "fecha venta", "fecha_de_venta", "date", "fventa", "fcha", "fec"],
        "amount": ["monto", "importe", "total", "amount", "precio", "valor", "venta"],
        "product": ["producto", "product", "sku", "articulo", "item"],
        "channel": ["canal", "channel", "medio", "origen", "source"],
    }
    normalized_cols = {c: _clean_header(c) for c in columns}
    mapping: Dict[str, Optional[str]] = {k: None for k in keywords.keys()}

    import difflib
    for col, norm in normalized_cols.items():
        for kind, kws in keywords.items():
            best_score = 0.0
            for kw in kws:
                score = difflib.SequenceMatcher(None, norm, _clean_header(kw)).ratio()
                if score > best_score:
                    best_score = score
            if best_score >= 0.6 and mapping[kind] is None:
                mapping[kind] = col
    return mapping


def parse_amount(monto_value: Any) -> float:
    if pd.isna(monto_value) or monto_value is None or str(monto_value).strip() == "":
        raise ValueError("Monto vacío")
    if isinstance(monto_value, str):
        s = monto_value.strip().replace(" ", "")
        if not s:
            raise ValueError("Monto vacío")
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError as e:
            raise ValueError(f"Monto inválido '{monto_value}': {e}")
    try:
        return float(monto_value)
    except Exception as e:
        raise ValueError(f"Monto inválido '{monto_value}': {e}")


def parse_date(date_value: Any) -> Optional[datetime]:
    if pd.isna(date_value) or date_value is None or str(date_value).strip() == "":
        return None
    dt = pd.to_datetime(date_value, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        dt = pd.to_datetime(date_value, dayfirst=False, errors="coerce")
    if pd.isna(dt):
        raise ValueError(f"Fecha inválida: {date_value}")
    return dt.to_pydatetime()


def _get_first_existing(row: pd.Series, candidates: List[str]) -> Any:
    for c in candidates:
        if c in row and pd.notna(row[c]):
            return row[c]
    return None


def map_row_to_sale_fields(row: pd.Series, column_map: Dict[str, Optional[str]]) -> Tuple[datetime, float, str, str]:
    # Date
    date_col = column_map.get("date")
    if date_col and date_col in row:
        date_value = row[date_col]
    else:
        date_value = _get_first_existing(row, ["date", "fecha", "fecha venta", "fecha_de_venta"])
    sale_date = parse_date(date_value)
    if sale_date is None:
        raise ValueError("Fecha no parseable")

    # Amount
    amount_col = column_map.get("amount")
    if amount_col and amount_col in row:
        monto_value = row[amount_col]
    else:
        monto_value = _get_first_existing(row, ["monto", "amount", "importe", "total", "valor"])
    monto_float = parse_amount(monto_value)

    # Product
    product_col = column_map.get("product")
    if product_col and product_col in row:
        prod_value = row[product_col]
    else:
        prod_value = _get_first_existing(row, ["producto", "product", "sku", "articulo", "item"]) or "Desconocido"
    prod_str = str(prod_value)

    # Channel
    channel_col = column_map.get("channel")
    if channel_col and channel_col in row:
        channel_value = row[channel_col]
    else:
        channel_value = _get_first_existing(row, ["channel", "canal", "medio", "origen"]) or "Upload"
    channel_str = str(channel_value)

    return sale_date, monto_float, prod_str, channel_str


# Prompt builder for explanations
EXPLAIN_PROMPT_TEMPLATE = (
    "Eres un analista de datos conciso. "
    "Contexto: {context_summary}\n\n"
    "Pide: 1) Resumen corto (1-2 frases). "
    "2) Causa probable (máx 3 frases). "
    "3) Recomendación accionable (1-2 pasos). "
    "Responde en español y sin numerar."
)


def build_explain_prompt(context: Dict[str, Any]) -> str:
    parts = []
    kpis = context.get("kpis", {})
    if kpis:
        parts.append("KPIs: " + ", ".join(f"{k}: {v}" for k, v in kpis.items()))
    top = context.get("top_changes", [])
    if top:
        parts.append("Top cambios: " + "; ".join(f"{t.get('key')} {t.get('change')}%" for t in top[:5]))
    anomalies = context.get("anomalies", [])
    if anomalies:
        parts.append("Anomalías: " + "; ".join(anomalies[:5]))
    context_summary = " | ".join(parts) or "Sin datos adicionales"
    return EXPLAIN_PROMPT_TEMPLATE.format(context_summary=context_summary)
