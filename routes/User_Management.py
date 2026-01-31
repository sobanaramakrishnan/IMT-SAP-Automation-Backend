from fastapi import APIRouter, HTTPException, status
from database import get_db_connection
from schemas import CreateUserRequest,LoginRequest
from passlib.context import CryptContext

router = APIRouter(prefix="/user", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
@router.post("/create-user", status_code=status.HTTP_201_CREATED)
def create_user(data: CreateUserRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM automation.users WHERE email = %s",
            (data.email,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        hashed_password = pwd_context.hash(data.password[:10])
        insert_query = """
            INSERT INTO automation.users (
                username,
                email,
                password,
                user_role,
                marked_for_deletion
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id;
        """

        cursor.execute(
            insert_query,
            (
                data.username,
                data.email,
                hashed_password, 
                data.user_role,
                "N"
            )
        )

        user_id = cursor.fetchone()["user_id"]
        conn.commit()

        return {
            "message": "User created successfully",
            "user_id": user_id,
            "email": data.email
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


@router.post("/login")
def login_user(data: LoginRequest):
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
            "user_role": user["user_role"]
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