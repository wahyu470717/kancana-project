from pydantic import BaseModel, EmailStr, validator, Field, model_validator
from typing import Optional, List
from datetime import datetime
import re

class UserResponse(BaseModel):
    id: int
    nip: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    jabatan: Optional[str] = None
    organization: Optional[str] = None
    no_telepon: Optional[str] = None
    is_active:  Optional[bool] = None
    is_verified: Optional[bool] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    last_activity: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleChangeRequest(BaseModel):
    role_name: str

class RoleListResponse(BaseModel):
    status: int
    message: str
    data: list[RoleRead]




# ============================================================================
# MANAGEMENT USERS SCHEMAS
# ============================================================================
class UserListResponse(BaseModel):
    status: int
    message: str
    data: List[UserResponse]
    page: int
    limit: int

class UserDetailResponse(BaseModel):
    status: int
    message: str
    data: UserResponse

# ✨ BARU - Schema untuk toggle active/inactive user
class ToggleUserActiveRequest(BaseModel):
    is_active: bool = Field(description="Set true untuk aktifkan, false untuk nonaktifkan")

class ToggleUserActiveResponse(BaseModel):
    status: int
    message: str
    data: UserResponse


class AdminUserCreate(BaseModel):
    nip: str = Field(min_length=5, max_length=50)
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=255)
    jabatan: str = Field(min_length=2, max_length=255)
    organization: str = Field(min_length=2, max_length=255)
    no_telepon: str = Field(min_length=10, max_length=20)
    role_name: str = Field(description="Role user (Super Admin, Eksekutif)")
    password: str = Field(min_length=8, max_length=20)
    
    @validator('nip')
    def validate_nip(cls, v):
        if not v.isdigit():
            raise ValueError('NIP harus berupa angka')
        return v

    # @validator('email')
    # def validate_email_domain(cls, v):
    #     if not v.lower().endswith('@jabarprov.go.id'):
    #         raise ValueError('Email harus menggunakan domain @jabarprov.go.id')
    #     return v.lower()

    @validator('no_telepon')
    def validate_phone(cls, v):
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^(\+62|62|0)[0-9]{9,12}$', cleaned):
            raise ValueError('Format nomor telepon tidak valid (contoh: 081234567890)')
        return cleaned

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8 or len(v) > 20:
            raise ValueError('Password harus 8 sampai 20 karakter')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kapital')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kecil')
        if not re.search(r'\d', v):
            raise ValueError('Password harus mengandung minimal 1 angka')
        if not re.search(r'[#?!/@&]', v):
            raise ValueError('Password harus mengandung minimal 1 karakter khusus (#, ?, !, /, @, &)')
        return v

    @validator('role_name')
    def validate_role(cls, v):
        allowed_roles = ["Super Admin", "Eksekutif"]
        if v not in allowed_roles:
            raise ValueError(f'Role harus salah satu dari: {", ".join(allowed_roles)}')
        return v


class AdminUserUpdate(BaseModel):
    nip: Optional[str] = Field(None, min_length=5, max_length=50)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=3, max_length=255)
    jabatan: Optional[str] = Field(None, min_length=2, max_length=255)
    organization: Optional[str] = Field(None, min_length=2, max_length=255)
    no_telepon: Optional[str] = Field(None, min_length=10, max_length=20)
    role_name: Optional[str] = None
    
    @validator('nip')
    def validate_nip(cls, v):
        if v and not v.isdigit():
            raise ValueError('NIP harus berupa angka')
        return v

    # @validator('email')
    # def validate_email_domain(cls, v):
    #     if v and not v.lower().endswith('@jabarprov.go.id'):
    #         raise ValueError('Email harus menggunakan domain @jabarprov.go.id')
    #     return v.lower() if v else v

    @validator('no_telepon')
    def validate_phone(cls, v):
        if v:
            cleaned = re.sub(r'[^\d+]', '', v)
            if not re.match(r'^(\+62|62|0)[0-9]{9,12}$', cleaned):
                raise ValueError('Format nomor telepon tidak valid (contoh: 081234567890)')
            return cleaned
        return v

    @validator('role_name')
    def validate_role(cls, v):
        if v:
            allowed_roles = ["Super Admin", "Eksekutif"]
            if v not in allowed_roles:
                raise ValueError(f'Role harus salah satu dari: {", ".join(allowed_roles)}')
        return v


class AdminUserCreateResponse(BaseModel):
    status: int
    message: str
    data: UserResponse


class AdminUserUpdateResponse(BaseModel):
    status: int
    message: str
    data: UserResponse
# ============================================================================
# REGISTRATION SCHEMAS
# ============================================================================
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None
    organization: Optional[str] = None

class UserCreate(UserBase):
    nip: str = Field(min_length=5, max_length=50)
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=255)
    jabatan: str = Field(min_length=2, max_length=255)
    organization: str = Field(min_length=2, max_length=255)  # Instansi
    no_telepon: str = Field(min_length=10, max_length=20)

    @validator('nip')
    def validate_nip(cls, v):
        if not v.isdigit():
            raise ValueError('NIP harus berupa angka')
        return v

    # @validator('email')
    # def validate_email_domain(cls, v):
    #     if not v.lower().endswith('@jabarprov.go.id'):
    #         raise ValueError('Email harus menggunakan domain @jabarprov.go.id')
    #     return v.lower()

    @validator('no_telepon')
    def validate_phone(cls, v):

        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^(\+62|62|0)[0-9]{9,12}$', cleaned):
            raise ValueError('Format nomor telepon tidak valid (contoh: 081234567890)')
        return cleaned

class User(UserBase):
    nip: str = Field(min_length=5, max_length=50)
    role_name: Optional[str] = None
    jabatan: Optional[str] = None
    no_telepon: Optional[str] = None


# ============================================================================
# SET PASSWORD SCHEMAS
# ============================================================================
class SetPasswordRequest(BaseModel):
    """Schema untuk user set password pertama kali"""
    token: str = Field(min_length=10)
    password: str = Field(min_length=8, max_length=20)
    confirm_password: str = Field(min_length=8, max_length=20)

    @validator('password')
    def validate_password_strength(cls, v):
        # Validasi panjang password
        if len(v) < 8 or len(v) > 20:
            raise ValueError('Password harus 8 sampai 20 karakter')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kapital')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kecil')

        if not re.search(r'\d', v):
            raise ValueError('Password harus mengandung minimal 1 angka')

        if not re.search(r'[#?!/@&]', v):
            raise ValueError('Password harus mengandung minimal 1 karakter khusus (#, ?, !, /, @, &)')

        return v

    @model_validator(mode='after')
    def validate_password_confirmation(self):
        if self.password != self.confirm_password:
            raise ValueError("Password dan konfirmasi password tidak cocok")
        return self



class SetPasswordResponse(BaseModel):
    status: int
    message: str


# ============================================================================
# VERIFICATION SCHEMAS - UPDATED
# ============================================================================
class VerificationRequest(BaseModel):
    """Schema untuk admin verifikasi user"""
    status: str = Field(pattern="^(approve|reject)$")
    notes: Optional[str] = None

class VerificationResponse(BaseModel):
    status: int
    message: str
    data: Optional['UserResponse'] = None

class PendingUserResponse(BaseModel):
    """Schema untuk list user pending"""
    id: int
    nip: Optional[str] = None
    username: str
    email: str
    full_name: str
    jabatan: Optional[str] = None
    organization: Optional[str] = None
    no_telepon: Optional[str] = None
    status_verifikasi: str
    created_at: datetime

    class Config:
        from_attributes = True

class PendingUsersListResponse(BaseModel):
    status: int
    message: str
    data: list[PendingUserResponse]
    total: int


# ============================================================================
# LOGIN & USER RESPONSE
# ============================================================================
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int # dalam menit
    message: str = "Login Berhasil"

class TokenData(BaseModel):
    username: Optional[str] = None
    ver: Optional[int] = None

# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    status: int
    message: str
    is_admin: bool

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=20)
    confirm_new_password: str = Field(min_length=8, max_length=20)

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8 or len(v) > 20:
            raise ValueError('Password harus 8 sampai 20 karakter')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kapital')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kecil')

        if not re.search(r'\d', v):
            raise ValueError('Password harus mengandung minimal 1 angka')

        if not re.search(r'[#?!/@&]', v):
            raise ValueError('Password harus mengandung minimal 1 karakter khusus (#, ?, !, /, @, &)')

        return v

    @model_validator(mode='after')
    def validate_password_confirmation(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("Password konfirmasi belum cocok dengan password baru")
        return self

class ResetPasswordResponse(BaseModel):
    status: int
    message: str

class ProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None
    organization: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str =  Field(min_length=8, max_length=20)
    confirm_new_password: str =  Field(min_length=8, max_length=20)

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8 or len(v) > 20:
            raise ValueError('Password harus 8 sampai 20 karakter')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kapital')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password harus mengandung minimal 1 huruf kecil')

        if not re.search(r'\d', v):
            raise ValueError('Password harus mengandung minimal 1 angka')

        if not re.search(r'[#?!/@&]', v):
            raise ValueError('Password harus mengandung minimal 1 karakter khusus (#, ?, !, /, @, &)')

        return v

    @model_validator(mode='after')
    def validate_password_confirmation(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("Password konfirmasi belum cocok dengan password baru")
        return self

class ChangePasswordResponse(BaseModel):
    status: int
    message: str

class VerifyUserRequest(BaseModel):
    user_id: int
    is_verified: bool = True
    is_active: bool = True

class VerifyUserResponse(BaseModel):
    status: int
    message: str
    data: UserResponse

class PendingUsersResponse(BaseModel):
    status: int
    message: str
    data: list[UserResponse]

class LogoutResponse(BaseModel):
    status: int
    message: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr


