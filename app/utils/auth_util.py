from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pwd_context.hash("test")
except Exception:
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        token_version: int = payload.get("ver", 0)
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial Tidak Valid"
            )
        return {"username": username, "ver": token_version}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid"
        )
    
def check_session_validity(user):
    if user.last_activity is None:
        return True
    
    time_diff = datetime.now(timezone.utc) - user.last_activity
    session_expire = timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
    
    if time_diff > session_expire:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi Anda telah berakhir karena tidak ada aktivitas. Silakan login kembali."
        )
    return True

def update_last_activity(db: Session, user):
    from app.domain.models import User
    db.query(User).filter(User.id == user.id).update(
        {"last_activity": datetime.now(timezone.utc)}
    )
    db.commit()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from app.domain.models import User

    try:
        token_data = decode_token(token)
        username = token_data["username"]
        token_version = token_data["ver"]
        
        user = db.query(User).filter(User.username == username).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pengguna tidak ditemukan"
            )

        if token_version != user.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pengguna tidak aktif"
            )
        
        check_session_validity(user)
        update_last_activity(db, user)

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid"
        )

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Pengguna tidak aktif")
    return current_user


async def get_current_user_with_role(
    current_user = Depends(get_current_active_user)
):
    allowed_roles = ["Super Admin", "Eksekutif"]
    
    if not current_user.role_name or current_user.role_name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Akses ditolak. Hanya {' atau '.join(allowed_roles)} yang dapat mengakses."
        )
    
    return current_user

def create_reset_password_token(email: str):

    expires_delta = timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "reset_password"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_reset_password_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "reset_password":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reset password tidak valid"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Token reset password tidak valid atau sudah kadaluarsa"
        )
    
async def require_admin(current_user = Depends(get_current_active_user)):
    if current_user.role_name != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this resource"
        )
    return current_user