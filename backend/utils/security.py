from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import hashlib

SECRET_KEY = "Admin@123PoojithaSuperSecretKey12345abcde86862f4a6b8c7d9e1f2a3b4c5d6e7f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash(password: str) -> str:
    """
    SHA-256 pre-hash to avoid bcrypt 72-byte limit
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(_prehash(password))


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(_prehash(password), hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
