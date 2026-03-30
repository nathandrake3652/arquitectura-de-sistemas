from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.user import create_user, get_users
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return get_users(db)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        ) from exc
