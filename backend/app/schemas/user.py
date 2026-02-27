from datetime import date, datetime
from pydantic import BaseModel, EmailStr, computed_field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    is_active: bool
    phone: str | None = None
    address: str | None = None
    profile_picture_url: str | None = None
    wallet_balance: float = 100.0
    is_black_member: bool = False
    black_member_since: datetime | None = None
    plus_flag: str | None = None
    spin_count_today: int = 0
    last_spin_date: date | None = None

    @computed_field
    @property
    def spins_remaining(self) -> int:
        """Calculate remaining spins for today (max 5 per day)."""
        today = date.today()
        if self.last_spin_date != today:
            return 5  # New day, full spins available
        return max(0, 5 - self.spin_count_today)

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None


class ForgotPasswordRequest(BaseModel):
    # ⚠️ INTENTIONALLY VULNERABLE (CTF: SQLi) — email is a plain str so that
    # injection payloads are not rejected by Pydantic's EmailStr validation.
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
