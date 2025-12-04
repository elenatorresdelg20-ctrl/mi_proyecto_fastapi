from app.core.config import get_settings

_settings = get_settings()

ENV = _settings.env
SECRET_KEY = _settings.secret_key
ALGORITHM = _settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.access_token_expire_minutes

# Optional Fernet key for encrypting sensitive fields in the DB
FERNET_KEY = _settings.fernet_key

# AI / HF
AI_PROVIDER = _settings.ai_provider
AI_API_URL = _settings.ai_api_url
AI_API_KEY = _settings.ai_api_key
AI_TIMEOUT = _settings.ai_timeout
AI_MAX_CONCURRENCY = _settings.ai_max_concurrency
COST_PER_1K_TOKENS = _settings.cost_per_1k_tokens

# Other
CHUNK_SIZE = _settings.chunk_size
