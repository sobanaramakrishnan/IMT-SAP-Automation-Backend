from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
from database import get_db_connection
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

router = APIRouter(tags=["DC Details"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
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
    cursor = None
    try:
        file_path = None
        if image is not None:
            file_ext = ""
            if image.filename and "." in image.filename:
                file_ext = os.path.splitext(image.filename)[1]
            filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as f:
                f.write(image.file.read())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO automation.dc_details (
                user_id,
                dc_number,
                part_name,
                part_number,
                quantity,
                weight,
                image_path
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
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/view-dc-details")
def get_dc_details():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                user_id,
                dc_id,
                dc_number,
                part_name,
                part_number,
                quantity,
                verified_status,
                weight
            FROM automation.dc_details
            ORDER BY dc_id DESC
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return {"message": "No DC details found", "data": []}
        return {
            "message": "DC details fetched successfully",
            "data": rows
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/verify-dc-details")
def verify_dc(
    dc_id: int = Form(...),
    user_id: int = Form(...),
    verification_status: str = Form(...),
    reviewed_weight: float = Form(...),
    reviewed_quantity: int = Form(...),
    process_type: str = Form(...),
    notification_status: str = Form(...)
):
    if verification_status not in ["Approved", "Rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'Approved' or 'Rejected'"
        )
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM automation.dc_details
            WHERE dc_id = %s
            """,
            (dc_id,)
        )
        dc = cursor.fetchone()
        if not dc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DC not found"
            )
        cursor.execute(
            """
            UPDATE automation.dc_details
            SET
                verified_by = %s,
                verified_at = %s,
                verified_status = %s,
                reviewed_weight = %s,
                reviewed_quantity = %s,
                process_type = %s,
                notification_sent = %s
            WHERE dc_id = %s
            """,
            (
                user_id,
                datetime.now(),
                verification_status,
                reviewed_weight,
                reviewed_quantity,
                process_type,
                notification_status,
                dc_id
            )
        )
        conn.commit()
        return {
            "message": f"DC {verification_status.lower()} successfully verified with process '{process_type}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/get-pending-count")
def get_pending_dc_count():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS pending_count
            FROM automation.dc_details
            WHERE TRIM(LOWER(verified_status)) = 'pending'
            """
        )
        result = cursor.fetchone()
        return {"pending_count": result["pending_count"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/get-verified-count")
def get_verified_dc_count():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS verified_count
            FROM automation.dc_details
            WHERE TRIM(LOWER(verified_status)) = 'verified'
            """
        )
        result = cursor.fetchone()
        return {"verified_count": result["verified_count"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()