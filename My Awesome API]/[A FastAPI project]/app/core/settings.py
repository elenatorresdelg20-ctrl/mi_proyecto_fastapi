import os
from typing import Optional

# Security / env
# In development a default is allowed for convenience, but in production the SECRET_KEY
# must be provided via environment variable to avoid accidental exposure.
SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV", "development")
if ENV == "production" and not SECRET_KEY:
	raise RuntimeError("SECRET_KEY must be set in production environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Optional Fernet key for encrypting sensitive fields in the DB
FERNET_KEY = os.getenv("FERNET_KEY")

# AI / HF
AI_PROVIDER = os.getenv("AI_PROVIDER", "cheap_api")
AI_API_URL = os.getenv("AI_API_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "8"))
AI_MAX_CONCURRENCY = int(os.getenv("AI_MAX_CONCURRENCY", "4"))
COST_PER_1K_TOKENS = float(os.getenv("COST_PER_1K_TOKENS", "0.4"))

# Other
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
