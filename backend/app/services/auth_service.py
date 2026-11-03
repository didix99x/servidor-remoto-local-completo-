"""
Authentication service for JWT token management and password hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User, UserRole
from app.schemas.auth import Token, TokenPayload, LoginRequest, RegisterRequest, UserResponse
from app.database import get_session


class AuthService:
    """Authentication service handling JWT tokens and password verification."""

    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            argon2__time_cost=self.settings.argon2_time_cost,
            argon2__memory_cost=self.settings.argon2_memory_cost,
            argon2__parallelism=self.settings.argon2_parallelism,
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2id."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        user_id: int,
        username: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )

        to_encode = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        return jwt.encode(to_encode, self.settings.secret_key, algorithm="HS256")

    def create_refresh_token(
        self,
        user_id: int,
        username: str,
        role: UserRole,
    ) -> str:
        """Create a JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_expire_days
        )

        to_encode = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }
        return jwt.encode(to_encode, self.settings.secret_key, algorithm="HS256")

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=["HS256"],
            )
            return TokenPayload(**payload)
        except JWTError:
            return None

    async def authenticate_user(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate a user by username and password."""
        result = await db.execute(
            select(User).where(User.username == username, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            role=role,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def update_last_login(self, db: AsyncSession, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login = datetime.now(timezone.utc)
        await db.flush()

    def create_token_response(
        self,
        user: User,
        remember_me: bool = False,
    ) -> Token:
        """Create token response for a user."""
        access_token_expires = (
            timedelta(days=self.settings.refresh_token_expire_days)
            if remember_me
            else timedelta(minutes=self.settings.access_token_expire_minutes)
        )

        access_token = self.create_access_token(
            user.id,
            user.username,
            user.role,
            access_token_expires,
        )
        refresh_token = self.create_refresh_token(user.id, user.username, user.role)

        expires_in = int(access_token_expires.total_seconds())

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create the auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service