from typing import Dict, Optional, Tuple, List
from sqlalchemy.orm import Session
import logging
from . import ai_client
from ..models.models import Sale

logger = logging.getLogger("saas_app.sales")


def bulk_insert_sales_chunked(
    df,
    tenant_id: int,
    db: Session,
    column_map: Dict[str, Optional[str]],
    chunk_size: int = 1000,
) -> Tuple[int, int]:
    total_inserted = 0
    errores = 0
    buffer: List[Sale] = []

    for idx, row in df.iterrows():
        try:
            from app.utils.helpers import map_row_to_sale_fields

            sale_date, monto_float, prod_str, channel_str = map_row_to_sale_fields(row, column_map)
        except Exception as e:
            errores += 1
            logger.warning("Error parsing row %s tenant %s: %s", idx, tenant_id, e)
            continue

        buffer.append(Sale(tenant_id=tenant_id, product=prod_str, amount=monto_float, date=sale_date, channel=channel_str))

        if len(buffer) >= chunk_size:
            try:
                db.bulk_save_objects(buffer)
                db.commit()
                total_inserted += len(buffer)
            except Exception as e:
                db.rollback()
                logger.exception("DB error inserting chunk for tenant %s: %s", tenant_id, e)
                errores += len(buffer)
            buffer = []

    if buffer:
        try:
            db.bulk_save_objects(buffer)
            db.commit()
            total_inserted += len(buffer)
        except Exception as e:
            db.rollback()
            logger.exception("DB error inserting final chunk for tenant %s: %s", tenant_id, e)
            errores += len(buffer)

    return total_inserted, errores
