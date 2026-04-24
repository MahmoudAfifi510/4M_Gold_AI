from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routes.dependencies import get_current_user
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(
            db,
            payload.first_name,
            payload.last_name,
            payload.username,
            payload.phone_number,
            payload.password,
        )
        login_result = auth_service.login(db, payload.username, payload.password)
        return {"access_token": login_result["access_token"], "token_type": "bearer", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        result = auth_service.login(db, payload.username, payload.password)
        return {"access_token": result["access_token"], "token_type": "bearer", "user": result["user"]}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.delete("/me")
def delete_account(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        auth_service.delete_user(db, current_user.id)
        return {"message": "Account deleted successfully."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
