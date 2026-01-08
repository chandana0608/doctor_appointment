from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..schemas import UserCreate, Token, Login
from ..database import get_session
from ..crud import create_user
from ..auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    from ..auth import get_user_by_email
    if get_user_by_email(session, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if not payload.full_name:
        raise HTTPException(status_code=422, detail="full_name is required")

    try:
        user, _ = create_user(
            session,
            payload.email,
            payload.password,
            payload.full_name,
            payload.role,
            payload.specialization,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if user.id is None:
        raise HTTPException(status_code=500, detail="User id not generated")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: Login, session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if user.id is None:
        raise HTTPException(status_code=500, detail="User id not generated")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}