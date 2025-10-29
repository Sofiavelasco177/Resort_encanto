"""
Quick one-off migration: add column `estado` to `inventario_habitacion` if it does not exist.
Safe to run multiple times.
Usage (Windows PowerShell):
  python -m scripts.migrate_add_inventario_estado
"""
from sqlalchemy import inspect, text

# Import app and db from run.py without starting the dev server
from run import app
from utils.extensions import db


def ensure_column_inventario_estado():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'inventario_habitacion' not in tables:
            print('Table inventario_habitacion not found. Nothing to do.')
            return
        cols = [c['name'] for c in inspector.get_columns('inventario_habitacion')]
        if 'estado' in cols:
            print("Column 'estado' already exists. Nothing to do.")
            return
        stmt = "ALTER TABLE inventario_habitacion ADD COLUMN estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente'"
        try:
            db.session.execute(text(stmt))
            db.session.commit()
            print("Column 'estado' added successfully with default 'Pendiente'.")
        except Exception as e:
            db.session.rollback()
            print('Failed to add column estado:', e)


if __name__ == '__main__':
    ensure_column_inventario_estado()
