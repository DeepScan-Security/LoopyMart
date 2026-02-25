"""
User profile and authentication API routes.
"""

import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.api.deps import get_current_user
from app.core.flags import get_flag
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserProfileUpdate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_admin=False,
        wallet_balance=100.0,  # Default wallet balance
        pending_cashback=0.0,  # New accounts start with no pending cashback
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    # Keep token claims consistent with login (frontend may rely on is_admin).
    token = create_access_token(user.id, extra={"is_admin": user.is_admin})
    return Token(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    token = create_access_token(user.id, extra={"is_admin": user.is_admin})
    return Token(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    response = UserResponse.model_validate(current_user)
    # Re-attach flag for Plus members so the UI can show it after a page refresh.
    if current_user.is_black_member:
        response.plus_flag = get_flag("mass_assignment_plus")
    return response


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update user profile (name, phone, address)."""
    # Get user with lock for update
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()
    
    # Update fields if provided
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.address is not None:
        user.address = data.address
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/profile-picture", response_model=UserResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Upload profile picture."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed.",
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit.",
        )
    
    # Save file to uploads directory
    from app.main import get_uploads_dir
    uploads_dir = get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"profile_{current_user.id}_{secrets.token_hex(8)}{file_extension}"
    file_path = uploads_dir / filename
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update user profile picture URL
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()
    user.profile_picture_url = f"/static/uploads/{filename}"
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate a password reset token and log it to the console.

    [INTENTIONALLY VULNERABLE – CTF challenge: SQL Injection]
    The ``email`` field is interpolated directly into a raw SQL query with no
    parameterization.  Pydantic's EmailStr validation has been intentionally
    removed from ForgotPasswordRequest so arbitrary payloads are accepted.

    Vulnerable sink:
        query = f"SELECT ... WHERE email = '{data.email}'"
        result = await db.execute(text(query))

    Example exploit payload (email field):
        ' OR '1'='1' --

    When the injected WHERE clause returns a row whose email column does not
    match the supplied input, the server detects the manipulation and includes
    the flag in the JSON response.

    CWE-89  Improper Neutralization of Special Elements used in an SQL Command
    """
    # ⚠️  VULNERABLE: email is concatenated into SQL without parameterization.
    query = f"SELECT id, email, is_active FROM users WHERE email = '{data.email}'"
    try:
        result = await db.execute(text(query))
    except Exception:
        # Malformed SQL (e.g., unmatched quotes) — return generic message.
        return {"message": "If the email exists, a reset link has been sent."}

    row = result.mappings().fetchone()

    if not row:
        return {"message": "If the email exists, a reset link has been sent."}

    # ✅ Injection detector: if the matched row’s email differs from what was
    # supplied, the WHERE clause was manipulated — expose the flag as reward.
    flag_extra: dict = {}
    if row["email"] != data.email:
        flag_val = get_flag("sqli_forgot")
        if flag_val:
            flag_extra = {"flag": flag_val}

    if not row["is_active"]:
        return {"message": "If the email exists, a reset link has been sent.", **flag_extra}

    # Continue with the normal reset-token flow using the resolved user id.
    user_id = row["id"]
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

    res2 = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = res2.scalar_one()
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires

    await db.commit()

    # Log token to console (dummy email)
    print(f"\n{'='*60}")
    print(f"PASSWORD RESET TOKEN (Dummy Email)")
    print(f"{'='*60}")
    print(f"Email: {user.email}")
    print(f"Reset Token: {reset_token}")
    print(f"Expires: {reset_token_expires}")
    print(f"Reset URL: http://localhost:5173/reset-password?token={reset_token}")
    print(f"{'='*60}\n")

    return {"message": "If the email exists, a reset link has been sent.", **flag_extra}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset password using token."""
    # Find user with this token
    result = await db.execute(
        select(User).where(User.reset_token == data.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    
    # Check if token is expired
    if not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    
    # Update password
    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    user = result.scalar_one()
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    await db.commit()
    
    return {"message": "Password reset successful. You can now login with your new password."}


@router.get("/profile-picture")
async def serve_profile_picture(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Return a profile-picture file from the uploads directory by filename.

    [INTENTIONALLY VULNERABLE – CTF challenge: Path Traversal]
    The ``filename`` query-parameter is joined directly to the uploads
    directory path with no canonicalization or boundary check.  An attacker
    can supply ``../`` sequences (raw or URL-encoded) to escape the uploads
    folder and read arbitrary files on the server.

    Example exploit:
        GET /auth/profile-picture?filename=../../../../../../tmp/path_traversal_flag.txt

    CWE-22  Improper Limitation of a Pathname to a Restricted Directory
    (Path Traversal)
    """
    from app.main import get_uploads_dir

    uploads_dir = get_uploads_dir()

    # ⚠️  VULNERABLE: filename is appended without resolving or validating
    # that the result stays inside uploads_dir.
    file_path = uploads_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return FileResponse(str(file_path), media_type="application/octet-stream")


@router.post("/upgrade-black", response_model=UserResponse)
async def upgrade_to_black(
    data: dict = Body(default={}),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Upgrade to LoopyMart Premium membership.

    [INTENTIONALLY VULNERABLE – CTF challenge: Mass Assignment]
    The optional JSON body is iterated and every key/value pair is blindly
    written onto the User model via setattr() before the eligibility check
    is evaluated.  A normal click sends no body and is rejected as
    "not eligible".  Supplying {"is_plus_eligible": true} in the request
    body sets that attribute on the in-memory user object, bypasses the
    gate, and triggers the upgrade — returning the flag in the response.

    Vulnerable sink:
        for k, v in data.items():
            setattr(user, k, v)        # ← mass-assignment, no allowlist

    CWE-915  Improperly Controlled Modification of Dynamically-Determined
             Object Attributes
    """
    if current_user.is_black_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a Plus member.",
        )

    # Get user with lock
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()

    # ⚠️  VULNERABLE: every key from the request body is set on the model
    # without any allowlist.  Attackers can set is_plus_eligible=true to
    # bypass the eligibility gate below, or tamper with any other attribute.
    for k, v in data.items():
        setattr(user, k, v)

    # Eligibility gate — blocked for normal users (no body sent from UI)
    if not getattr(user, "is_plus_eligible", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not eligible for LoopyMart Plus membership.",
        )

    # Proceed with upgrade
    user.is_black_member = True
    user.black_member_since = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    response = UserResponse.model_validate(user)
    response.plus_flag = get_flag("mass_assignment_plus")
    return response
