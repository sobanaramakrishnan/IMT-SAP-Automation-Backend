from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
from database import get_db_connection
import os
import uuid
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(tags=["DC Details"])


UPLOAD_DIR = os.getenv("DC_FORMS")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/create-dc-details")
def submit_dc_details(
    user_id: int = Form(...),
    dc_number: str = Form(...),
    part_name: str = Form(...),
    part_number: str = Form(...),
    quantity: int = Form(...),
    weight: float = Form(...),
    image: Optional[UploadFile] = File(None)
):
    conn = None
    try:
        file_path = None
        if image is not None:
            file_ext = image.filename.split(".")[-1]
            filename = f"{user_id}.{file_ext}"  
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(image.file.read())

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO automation.dc_details (
                user_id, dc_number, part_name, part_number,
                quantity, weight, image_path
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                dc_number,
                part_name,
                part_number,
                quantity,
                weight,
                file_path  
            )
        )

        conn.commit()

        return {"message": "DC details submitted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if conn:
            cursor.close()
            conn.close()

@router.get("/view-dc-details")
def get_dc_details():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                dc_number,
                part_name,
                part_number,
                quantity,
                weight
            FROM automation.dc_details
            """,
        
        )

        rows = cursor.fetchall()

        if not rows:
            return {
                "message": "No DC details found",
                "data": rows
            }

        return {
            "message": "DC details fetched successfully",
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


