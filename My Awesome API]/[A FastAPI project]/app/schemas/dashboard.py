from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    dtype: str


class UploadPreviewResponse(BaseModel):
    tenant: str
    file_name: str
    columns: List[ColumnInfo]
    sample_rows: List[Dict[str, Any]]
    total_rows: int


class KpiCard(BaseModel):
    label: str
    value: float
    change: float


class TrendPoint(BaseModel):
    label: str
    value: float


class BreakdownRow(BaseModel):
    name: str
    value: float
    change: float


class AnalysisDashboardResponse(BaseModel):
    tenant: str
    kpis: List[KpiCard]
    trend: List[TrendPoint]
    breakdown: List[BreakdownRow]


class ForecastSeriesPoint(BaseModel):
    label: str
    actual: Optional[float] = None
    forecast: Optional[float] = None


class ForecastDashboardResponse(BaseModel):
    tenant: str
    horizon: str
    series: List[ForecastSeriesPoint]
    meta: Dict[str, Any]


class ReportTableRow(BaseModel):
    segment: str
    revenue: float
    growth: float
    share: float


class ReportDashboardResponse(BaseModel):
    tenant: str
    highlights: List[KpiCard]
    table: List[ReportTableRow]


class SalesFunnelStage(BaseModel):
    stage: str
    value: float
    conversion: float


class SalesDashboardResponse(BaseModel):
    tenant: str
    funnel: List[SalesFunnelStage]
    top_products: List[BreakdownRow]
