#!/usr/bin/env python
"""
Script para generar datos de ejemplo para el forecast.
Simula histórico de ventas de los últimos 90 días.
"""

import sys
from datetime import datetime, timedelta
from random import randint, uniform
from sqlalchemy.orm import Session

sys.path.insert(0, "/Users/elena/mi_proyecto_fastapi/My Awesome API]/[A FastAPI project]")

from app.core.db import SessionLocal, engine, Base
from app.models.models import Tenant, Sale


def seed_example_data():
    """Siembra datos de ejemplo en la BD."""
    db = SessionLocal()
    
    try:
        # Crear tenant si no existe
        tenant = db.query(Tenant).filter(Tenant.code == "demo_001").first()
        if not tenant:
            tenant = Tenant(
                name="Demo Store",
                code="demo_001",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            print(f"✓ Tenant creado: {tenant.code}")
        else:
            print(f"✓ Tenant ya existe: {tenant.code}")
        
        # Verificar si ya hay datos
        existing_sales = db.query(Sale).filter(Sale.tenant_id == tenant.id).count()
        if existing_sales > 0:
            print(f"✓ Ya hay {existing_sales} ventas en la BD")
            return
        
        # Generar histórico de 90 días (desde -90 hasta hoy)
        products = ["iPhone 15", "iPad Pro", "MacBook Air", "AirPods Pro", "Apple Watch"]
        channels = ["Online", "Tienda Física", "Distribuidor"]
        
        # Usar datetime.now() en lugar de utcnow() para que sea más actual
        base_date = datetime.now() - timedelta(days=90)
        
        for day_offset in range(90):
            current_date = base_date + timedelta(days=day_offset)
            
            # Generar 5-15 transacciones por día
            num_transactions = randint(5, 15)
            
            for _ in range(num_transactions):
                sale = Sale(
                    tenant_id=tenant.id,
                    date=current_date + timedelta(hours=randint(0, 23), minutes=randint(0, 59)),
                    product=products[randint(0, len(products)-1)],
                    amount=uniform(100, 3000),
                    channel=channels[randint(0, len(channels)-1)]
                )
                db.add(sale)
        
        db.commit()
        
        # Estadísticas
        total_sales = db.query(Sale).filter(Sale.tenant_id == tenant.id).count()
        total_amount = db.query(
            __import__('sqlalchemy').func.sum(Sale.amount)
        ).filter(Sale.tenant_id == tenant.id).scalar() or 0
        
        print(f"✓ Se crearon {total_sales} ventas de ejemplo")
        print(f"✓ Monto total: ${total_amount:,.2f}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Generando datos de ejemplo para Forecast")
    print("=" * 70)
    
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    
    seed_example_data()
    
    print("=" * 70)
    print("✓ Datos de ejemplo cargados exitosamente")
    print("=" * 70)
