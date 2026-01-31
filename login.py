
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db_connection

from schemas import LoginRequest


router = APIRouter(prefix="/auth", tags=["Auth"])



@router.post("/login")
def login(data: LoginRequest):
    user = db.query(User).filter(
        User.email == data.email,
        User.marked_for_deletion != "Y"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.user_role
    }
