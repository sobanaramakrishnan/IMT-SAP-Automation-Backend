from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Query
from typing import Optional
from database import get_db_connection
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
import os
from pathlib import Path
from fastapi.responses import FileResponse



load_dotenv()

router = APIRouter(tags=["DC Details"])

BASE_DIR = os.getenv("BASE_DIR")
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

@router.get("/download-dc-details")
def download_dc_details_excel(
    user_id: int | None = Query(default=None)
):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                created_at as "Created Date", 
                dc_number as "DC Number", 
                part_number as "Part Number", 
                part_name as "Part Name",
                quantity as "Quantity", 
                weight as "Weight", 
                process_type as "Process Type",
                verified_status as "Verified Status", 
                verified_by as "Verified By"
            FROM automation.dc_details
        """

        params = ()

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No DC details found to export"
            )
        df = pd.DataFrame(rows)
        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:
            df.to_excel(
                writer,
                index=False,
                sheet_name="DC Details"
            )

            worksheet = writer.sheets["DC Details"]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            # Automatically adjust column widths
            for column_cells in worksheet.columns:
                max_length = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in column_cells
                )

                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(max_length + 2, 40)

        excel_buffer.seek(0)
        file_name = f"DC_Details_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        return StreamingResponse(
            excel_buffer,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition":
                    f'attachment; filename="{file_name}"'
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Excel: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/view-dc-image")
def view_dc_image(dc_id: int = Query(...)):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT image_path
            FROM automation.dc_details
            WHERE dc_id = %s
            """,
            (dc_id,)
        )

        record = cursor.fetchone()

        if not record or not record["image_path"]:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT image_path
            FROM automation.dc_details
            WHERE dc_id = %s
        """

        cursor.execute(query, (dc_id,))
        record = cursor.fetchone()

        if not record:
            raise HTTPException(
                status_code=404,
                detail="DC details not found"
            )

        image_path = record["image_path"]

        if not image_path or not image_path.strip():
            raise HTTPException(
                status_code=404,
                detail="No image uploaded for this DC"
            )
        stored_path = Path(image_path)

        if stored_path.is_absolute():
            resolved_path = stored_path.resolve()
        
        if not resolved_path.is_relative_to(UPLOAD_DIR):
            raise HTTPException(
                status_code=403,
                detail="Invalid image path"
            )

        if not resolved_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Image file not found on server"
            )

        return FileResponse(
            path=str(resolved_path),
            media_type="image/" + (
                resolved_path.suffix.lower().lstrip(".")
                if resolved_path.suffix.lower() in {
                    ".png", ".jpg", ".jpeg", ".gif", ".webp"
                }
                else "jpeg"
            ),
            filename=resolved_path.name,
            content_disposition_type="inline"
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve DC image"
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()