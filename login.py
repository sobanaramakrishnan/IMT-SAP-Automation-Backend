from fastapi import APIRouter, HTTPException, status
from database import get_db_connection
from schemas import LoginRequest
from passlib.context import CryptContext

router = APIRouter(tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
def login(data: LoginRequest):
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, username, email, password, user_role
            FROM automation.users
            WHERE email = %s
              AND marked_for_deletion = 'N'
            """,
            (data.email,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not pwd_context.verify(data.password[:72], user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        return {
            "message": "Login successful",
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["user_role"]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    finally:
        if conn:
            cursor.close()
            conn.close()
