# Makefile - útiles para desarrollo

env:
	@echo "Activar venv: source /Users/elena/mi_proyecto_fastapi/venv/bin/activate"

alembic-upgrade:
	@echo "Ejecutando alembic upgrade head (asegúrate de tener BACKUP y FERNET_KEY)"
	alembic upgrade head

encrypt-dry-run:
	@echo "Dry-run: revisar qué campos se cifrarían"
	python "scripts/encrypt_external_integrations.py" --dry-run

encrypt-apply:
	@echo "APLICAR: cifrar valores en la BD (asegúrate de BACKUP y FERNET_KEY)"
	python "scripts/encrypt_external_integrations.py" --apply
