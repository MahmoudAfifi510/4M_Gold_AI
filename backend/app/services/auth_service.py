from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.schema import User


class AuthService:
    def register_user(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        username: str,
        phone_number: str,
        password: str,
    ) -> User:
        existing = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if existing:
            raise ValueError("Username already exists.")
        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            username=username.strip(),
            phone_number=phone_number.strip(),
            password_hash=hash_password(password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def authenticate(self, session: Session, username: str, password: str) -> User:
        user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password.")
        return user

    def login(self, session: Session, username: str, password: str) -> dict:
        user = self.authenticate(session, username, password)
        token = create_access_token(str(user.id))
        return {"access_token": token, "user": user}

    def delete_user(self, session: Session, user_id: int) -> None:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise ValueError("User not found.")
        session.delete(user)
        session.commit()
