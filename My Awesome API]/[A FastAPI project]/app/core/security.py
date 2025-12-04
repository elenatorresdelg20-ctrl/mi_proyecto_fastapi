from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from .settings import SECRET_KEY, ENV, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    return User(
        id=1,
        username=username,
        full_name="",
        email="",
        hashed_password=get_password_hash(password),
        tenant_id=1,
        is_active=True,
        is_tenant_admin=False,
    )

def create_access_token(user_id: int):
    to_encode = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user():
    return {
        "id": 1,
        "username": "demo",
        "full_name": "Demo User",
        "email": "demo@example.com",
        "tenant_id": 1,
        "is_active": True,
        "is_tenant_admin": False,
    }
