"""
KYC API routes.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pathlib import Path
import secrets

from app.api.deps import require_admin, get_current_user
from app.db.kyc_mongo import kyc_create, kyc_get_by_user, kyc_list_all, kyc_update
from app.models.user import User
from app.schemas.kyc import KYCCreate, KYCResponse, KYCStatusUpdate

router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.post("", response_model=KYCResponse, status_code=status.HTTP_201_CREATED)
async def create_kyc(
    data: KYCCreate,
    current_user: User = Depends(get_current_user),
) -> KYCResponse:
    """Create KYC record for current user."""
    # Check if KYC already exists
    existing = await kyc_get_by_user(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC record already exists. Upload document to update.",
        )
    
    # Validate document type
    if data.document_type not in ["AADHAR", "PAN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document type must be AADHAR or PAN.",
        )
    
    kyc = await kyc_create(
        user_id=current_user.id,
        document_type=data.document_type,
        document_number=data.document_number,
    )
    
    return KYCResponse(
        id=kyc["id"],
        user_id=kyc["user_id"],
        document_type=kyc["document_type"],
        document_number=kyc["document_number"],
        document_image_url=kyc.get("document_image_url"),
        status=kyc["status"],
        created_at=kyc["created_at"].isoformat(),
        updated_at=kyc["updated_at"].isoformat(),
    )


@router.post("/upload-document", response_model=KYCResponse)
async def upload_kyc_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> KYCResponse:
    """Upload KYC document image."""
    # Get existing KYC
    kyc = await kyc_get_by_user(current_user.id)
    if not kyc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC record not found. Create KYC record first.",
        )
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, GIF, WebP, and PDF files are allowed.",
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit.",
        )
    
    # Save file to uploads directory
    from app.main import get_uploads_dir
    uploads_dir = get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"kyc_{current_user.id}_{secrets.token_hex(8)}{file_extension}"
    file_path = uploads_dir / filename
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update KYC with document URL
    document_url = f"/static/uploads/{filename}"
    updated_kyc = await kyc_update(
        kyc["id"],
        document_image_url=document_url,
    )
    
    if not updated_kyc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update KYC record.",
        )
    
    return KYCResponse(
        id=updated_kyc["id"],
        user_id=updated_kyc["user_id"],
        document_type=updated_kyc["document_type"],
        document_number=updated_kyc["document_number"],
        document_image_url=updated_kyc.get("document_image_url"),
        status=updated_kyc["status"],
        created_at=updated_kyc["created_at"].isoformat(),
        updated_at=updated_kyc["updated_at"].isoformat(),
    )


@router.get("/me", response_model=KYCResponse | None)
async def get_my_kyc(
    current_user: User = Depends(get_current_user),
) -> KYCResponse | None:
    """Get KYC record for current user."""
    kyc = await kyc_get_by_user(current_user.id)
    
    if not kyc:
        return None
    
    return KYCResponse(
        id=kyc["id"],
        user_id=kyc["user_id"],
        document_type=kyc["document_type"],
        document_number=kyc["document_number"],
        document_image_url=kyc.get("document_image_url"),
        status=kyc["status"],
        created_at=kyc["created_at"].isoformat(),
        updated_at=kyc["updated_at"].isoformat(),
    )


@router.get("/all", response_model=list[KYCResponse])
async def list_all_kyc(
    current_user: User = Depends(require_admin),
) -> list[KYCResponse]:
    """List all KYC records (admin only)."""
    kyc_records = await kyc_list_all()
    
    return [
        KYCResponse(
            id=kyc["id"],
            user_id=kyc["user_id"],
            document_type=kyc["document_type"],
            document_number=kyc["document_number"],
            document_image_url=kyc.get("document_image_url"),
            status=kyc["status"],
            created_at=kyc["created_at"].isoformat(),
            updated_at=kyc["updated_at"].isoformat(),
        )
        for kyc in kyc_records
    ]


@router.put("/{kyc_id}/status", response_model=KYCResponse)
async def update_kyc_status(
    kyc_id: str,
    data: KYCStatusUpdate,
    current_user: User = Depends(require_admin),
) -> KYCResponse:
    """Update KYC status (admin only)."""
    # Validate status
    if data.status not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be VERIFIED or REJECTED.",
        )
    
    updated_kyc = await kyc_update(
        kyc_id,
        status=data.status,
        remarks=data.remarks,
    )
    
    if not updated_kyc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC record not found.",
        )
    
    return KYCResponse(
        id=updated_kyc["id"],
        user_id=updated_kyc["user_id"],
        document_type=updated_kyc["document_type"],
        document_number=updated_kyc["document_number"],
        document_image_url=updated_kyc.get("document_image_url"),
        status=updated_kyc["status"],
        created_at=updated_kyc["created_at"].isoformat(),
        updated_at=updated_kyc["updated_at"].isoformat(),
    )
