#!/usr/bin/env python3
"""Lista filas de la tabla `external_integrations` y muestra si sus campos están cifrados.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "[A FastAPI project]"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.db import SessionLocal
from app.models.models import ExternalIntegration


def main():
    db = SessionLocal()
    try:
        rows = db.query(ExternalIntegration).all()
    except Exception as e:
        print("Error leyendo tabla external_integrations:", e)
        return
    if not rows:
        print("No hay filas en external_integrations.")
        return
    print(f"Encontradas {len(rows)} filas en external_integrations:")
    for r in rows:
        print(f"- id={r.id} provider={r.provider} name={r.name} is_active={r.is_active}")
        for field in ("api_key", "access_token", "refresh_token"):
            val = getattr(r, field)
            if val is None:
                status = "(none)"
            elif isinstance(val, str) and val.startswith("enc:"):
                status = "(encrypted)"
            else:
                status = f"(plain: {str(val)[:80]})"
            print(f"    {field}: {status}")

    # show sample count per provider
    providers = {}
    for r in rows:
        providers[r.provider] = providers.get(r.provider, 0) + 1
    print("Resumen por provider:")
    for p, c in providers.items():
        print(f"  {p}: {c}")


if __name__ == '__main__':
    main()
