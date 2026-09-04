from datetime import datetime, timedelta, timezone
from typing import List, Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import AppUser, RBACRole

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

# Security helpers using direct bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Refresh token defaults to 7 days
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

# Dependency injections for authentication and authorization
def require_authenticated_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> AppUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("sub")
    token_type: str = payload.get("type", "access")
    
    if email is None or token_type == "refresh":
        raise credentials_exception
        
    user = db.query(AppUser).filter(AppUser.email == email).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user


def get_optional_authenticated_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(optional_oauth2_scheme)
) -> Optional[AppUser]:
    if not token:
        return None
    try:
        payload = verify_token(token)
        if payload is None:
            return None
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if email is None or token_type == "refresh":
            return None
        user = db.query(AppUser).filter(AppUser.email == email).first()
        if user is None or not user.is_active:
            return None
        return user
    except Exception:
        return None


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: AppUser = Depends(require_authenticated_user)
    ) -> AppUser:
        # Superuser bypasses all role checks
        if current_user.is_superuser:
            return current_user
            
        user_role_names = [role.name for role in current_user.roles]
        for role in self.allowed_roles:
            if role in user_role_names:
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have required permissions (needs one of: {', '.join(self.allowed_roles)})"
        )

# Helper authorization functions
def require_role(allowed_roles: List[str]):
    return RoleChecker(allowed_roles)

def require_admin():
    return RoleChecker(["ADMIN"])
