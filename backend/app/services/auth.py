from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import users
from app.schemas.auth import UserCreate


def register_user(db: Session, payload: UserCreate) -> User:
    user = User(id=str(uuid4()), email=payload.email.lower(), password_hash=hash_password(payload.password))
    return users.create(db, user)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = users.get_by_email(db, email)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user
