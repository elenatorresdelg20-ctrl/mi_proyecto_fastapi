#!/usr/bin/env python3
"""Script para cifrar campos sensibles en `external_integrations` usando Fernet.

Características añadidas:
- `--dry-run` (por defecto) lista cambios sin escribir a la BD.
- `--yes` aplica los cambios reales sin pedir confirmación adicional.
- Logging y resumen de cambios (IDs y campos afectados).

Uso:
  export FERNET_KEY=...  # required para aplicar cambios
  # dry-run (por defecto): muestra lo que cambiaría
  python scripts/encrypt_external_integrations.py --dry-run
  # aplicar cambios (confirmar con --yes)
  python scripts/encrypt_external_integrations.py --yes

El script marca los valores cifrados con el prefijo `enc:` para que sea idempotente.
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import exc as sa_exc

# Ensure package importable (project subfolder)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "[A FastAPI project]"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.crypto import get_fernet
from app.core.db import SessionLocal
from app.models.models import ExternalIntegration


logger = logging.getLogger("encrypt_external_integrations")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def scan_and_prepare(db: Session, fernet) -> Tuple[int, List[Dict]]:
    """Escanea filas y devuelve (cantidad_total_campos_afectados, lista_de_cambios).

    Cada entrada en la lista tiene: {id, field, old_value, new_value_preview}.
    """
    try:
        rows = db.query(ExternalIntegration).all()
    except sa_exc.OperationalError as e:
        logger.warning("No se pudo leer `external_integrations`: %s", e)
        return 0, []
    changes = []
    count = 0
    for r in rows:
        for field in ("api_key", "access_token"):
            val = getattr(r, field)
            if val is None:
                continue
            if isinstance(val, str) and val.startswith("enc:"):
                continue
            try:
                token = fernet.encrypt(str(val).encode()).decode()
                changes.append({
                    "id": r.id,
                    "field": field,
                    "old": str(val)[:200],
                    "new_preview": ("enc:" + token)[:200],
                })
                count += 1
            except Exception as e:
                logger.error("Fallo al preparar cifrado para id=%s, campo=%s: %s", r.id, field, e)
    return count, changes


def apply_changes(db: Session, fernet, changes: List[Dict]) -> int:
    """Aplica cambios ya preparados; devuelve número de campos actualizados."""
    updated = 0
    try:
        for change in changes:
            r = db.query(ExternalIntegration).get(change["id"])
            if not r:
                continue
            field = change["field"]
            val = getattr(r, field)
            if val is None:
                continue
            if isinstance(val, str) and val.startswith("enc:"):
                continue
            token = fernet.encrypt(str(val).encode()).decode()
            setattr(r, field, "enc:" + token)
            updated += 1
        if updated > 0:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return updated


def parse_args():
    p = argparse.ArgumentParser(description="Cifra `external_integrations` usando FERNET_KEY")
    p.add_argument("--dry-run", action="store_true", default=True, help="Mostrar cambios sin escribir (por defecto)")
    p.add_argument("--apply", dest="apply", action="store_true", help="Aplicar los cambios a la BD (reemplaza --dry-run)")
    p.add_argument("--yes", action="store_true", help="Confirmar sin pedir interacción")
    return p.parse_args()


def main():
    args = parse_args()
    # normalize flags: --apply overrides --dry-run
    dry_run = not args.apply

    fernet = get_fernet()
    if not fernet:
        logger.error("FERNET_KEY no está configurada o cryptography no disponible. Abortando.")
        return

    db: Session = SessionLocal()
    try:
        count, changes = scan_and_prepare(db, fernet)
        if count == 0:
            logger.info("No hay campos pendientes de cifrar.")
            return

        logger.info("Se han detectado %d campos a cifrar en %d filas.", count, len({c['id'] for c in changes}))
        # mostrar un resumen (IDs y campos)
        for c in changes[:100]:
            logger.info("id=%s field=%s old_preview=%s", c["id"], c["field"], c["old"])

        if dry_run:
            logger.info("Dry-run activado: no se escribirán cambios.")
            return

        # en modo apply: confirmar
        if not args.yes:
            ans = input("Confirmar aplicación de cambios a la BD? (yes/no): ").strip().lower()
            if ans not in ("y", "yes"):
                logger.info("Operación cancelada por usuario.")
                return

        # aplicar cambios
        updated = apply_changes(db, fernet, changes)
        logger.info("Actualizados %d campos cifrados.", updated)
    finally:
        db.close()


if __name__ == '__main__':
    main()
