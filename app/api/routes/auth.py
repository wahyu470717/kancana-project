from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.service.auth_service import AuthService
from app.api.schemas.auth_schema import (
    UserCreate, UserLogin, UserResponse, Token,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ProfileUpdateRequest,
    ChangePasswordRequest, ChangePasswordResponse,
    RoleListResponse, RoleChangeRequest,
    LogoutResponse,
    VerificationRequest, VerificationResponse, 
    PendingUsersListResponse, SetPasswordResponse, SetPasswordRequest,
    UserListResponse, UserDetailResponse, AdminUserCreateResponse, AdminUserUpdateResponse,
    ToggleUserActiveRequest, ToggleUserActiveResponse,
    AdminUserCreate, AdminUserUpdate
)
from app.api.schemas.response_schemas import success_response, error_response
from app.utils.auth_util import get_current_active_user
from app.domain.models import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# ============================================================================
# REGISTER & LOGIN
# ============================================================================
@router.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        service = AuthService(db)
        new_user = service.register_user(user)
        
        return {
            "status": "success",
            "code": 201,
            "message": "User berhasil terdaftar. Menunggu verifikasi administrator.",
            "data": {
                "id": new_user.id,
                "nip": new_user.nip,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "jabatan": new_user.jabatan,
                "organization": new_user.organization,
                "no_telepon": new_user.no_telepon,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
                "role_name": new_user.role_name,
                "last_activity": new_user.last_activity,
                "created_at": new_user.created_at,
                "updated_at": new_user.updated_at
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "code": 500, "message": "Internal server error"}
        )
    
@router.post("/set-password", response_model=SetPasswordResponse)
def set_password(
    payload: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        service = AuthService(db)
        service.set_password_from_token(payload)
        return SetPasswordResponse(
            status=status.HTTP_200_OK,
            message="Password berhasil dibuat! Silakan login dengan username dan password Anda."
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Set password error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Gagal membuat password", 500)
        )


@router.post("/login")
def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user dan dapatkan access token"""
    try:
        service = AuthService(db)
        result = service.authenticate_user(login_data)
        return success_response(
            data={
                "access_token": result["access_token"],
                "token_type": "bearer",
                "expires_in": result["expires_in"],
                "user": UserResponse.from_orm(result["user"])
            },
            message="Login berhasil"
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e.detail, e.status_code))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Logout user"""
    try:
        service = AuthService(db)
        service.logout_user(current_user)
        return LogoutResponse(
            status=status.HTTP_200_OK,
            message="Logout berhasil"
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )



# ============================================================================
# USER INFO & PROFILE
# ============================================================================
@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Dapatkan informasi user saat ini"""
    return success_response(
        data=UserResponse.from_orm(current_user),
        message="Data user berhasil diambil"
    )


@router.patch("/me/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        service = AuthService(db)
        updated_user = service.update_user_profile(current_user, payload)
        return success_response(
            data=UserResponse.from_orm(updated_user),
            message="Profile berhasil diperbarui"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )

@router.get("/users")
def get_all_users(
    limit: int = Query(50, ge=1, le=100, description="Jumlah data per halaman"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    search: str = Query(None, description="Cari berdasarkan nama, username, email, NIP, jabatan, atau instansi"),
    role: str = Query(None, description="Filter berdasarkan role (Super Admin, Eksekutif)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        if current_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya administrator yang dapat mengakses resource ini"
            )
        
        calculated_offset = (page - 1) * limit
        
        service = AuthService(db)
        users, total = service.get_all_users(
            limit=limit,
            page=calculated_offset,
            search=search,
            role_filter=role
        )
        
        return UserListResponse(
            status=status.HTTP_200_OK,
            message="Daftar user berhasil diambil",
            data=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get all users error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )

@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        if current_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya administrator yang dapat mengakses resource ini"
            )
        
        service = AuthService(db)
        user = service.get_user_by_id(user_id)
            
        return UserDetailResponse(
            status=status.HTTP_200_OK,
            message="Detail user berhasil diambil",
            data=UserResponse.from_orm(user)
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get user detail error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )

@router.patch("/users/{user_id}/toggle-active", response_model=ToggleUserActiveResponse)
def toggle_user_active(
    user_id: int,
    payload: ToggleUserActiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        service = AuthService(db)
        updated_user = service.toggle_user_active(current_user, user_id, payload.is_active)
        
        action = "diaktifkan" if payload.is_active else "dinonaktifkan"
        return ToggleUserActiveResponse(
            status=status.HTTP_200_OK,
            message=f"User berhasil {action}",
            data=UserResponse.from_orm(updated_user)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Toggle user active error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.post("/users", response_model=AdminUserCreateResponse, status_code=201)
def create_user_by_admin(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        service = AuthService(db)
        new_user = service.create_user_by_admin(current_user, user_data)
        
        return AdminUserCreateResponse(
            status=status.HTTP_201_CREATED,
            message="User berhasil dibuat",
            data=UserResponse.from_orm(new_user)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Create user by admin error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.put("/users/{user_id}", response_model=AdminUserUpdateResponse)
def update_user_by_admin(
    user_id: int,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        service = AuthService(db)
        updated_user = service.update_user_by_admin(current_user, user_id, update_data)
        
        return AdminUserUpdateResponse(
            status=status.HTTP_200_OK,
            message="User berhasil diupdate",
            data=UserResponse.from_orm(updated_user)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Update user by admin error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )
# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================
@router.post("/me/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        service = AuthService(db)
        service.change_user_password(current_user, payload)
        return ChangePasswordResponse(
            status=status.HTTP_200_OK,
            message="Password berhasil diperbarui"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        service = AuthService(db)
        is_admin = service.request_password_reset(payload)
        return ForgotPasswordResponse(
            status=status.HTTP_200_OK,
            message="Jika email terdaftar, link reset password akan dikirim dalam beberapa menit.",
            is_admin=is_admin
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Gagal memproses permintaan", 500)
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_endpoint(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        service = AuthService(db)
        service.reset_password(payload)
        return ResetPasswordResponse(
            status=status.HTTP_200_OK,
            message="Password berhasil direset. Silakan login dengan password baru Anda."
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Gagal reset password", 500)
        )
    

# ============================================================================
# ROLE MANAGEMENT
# ============================================================================
@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: RoleChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        service = AuthService(db)
        updated_user = service.change_user_role(current_user, user_id, payload.role_name)
        return success_response(
            data=UserResponse.from_orm(updated_user),
            message="Role user berhasil diperbarui"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.get("/roles", response_model=RoleListResponse)
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List semua role - Super Admin only"""
    try:
        if current_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya administrator yang dapat mengakses resource ini"
            )

        service = AuthService(db)
        roles = service.list_roles()
        return RoleListResponse(
            status=status.HTTP_200_OK,
            message="Daftar role berhasil diambil",
            data=roles
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get roles error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


# ============================================================================
# VERIFICATION ENDPOINTS
# ============================================================================
@router.get("/users/pending", response_model=PendingUsersListResponse)
def get_pending_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        if current_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya administrator yang dapat mengakses resource ini"
            )

        service = AuthService(db)
        users, total = service.get_pending_users_for_verification(limit, offset)

        from app.api.schemas.auth_schema import PendingUserResponse
        return PendingUsersListResponse(
            status=status.HTTP_200_OK,
            message="Daftar user pending berhasil diambil",
            data=[PendingUserResponse.from_orm(user) for user in users],
            total=total
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get pending users error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )


@router.post("/users/{user_id}/verify", response_model=VerificationResponse)
def verify_user(
    user_id: int,
    payload: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verifikasi user - approve atau reject"""
    try:
        if current_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya administrator yang dapat memverifikasi user"
            )
        
        service = AuthService(db)
        verified_user = service.verify_user(current_user, user_id, payload)

        return VerificationResponse(
            status=status.HTTP_200_OK,
            message=f"User berhasil di-{payload.status}",
            data=UserResponse.from_orm(verified_user)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Verify user error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Gagal memverifikasi user", 500)
        )

# ============================================================================
# TOKEN VALIDATION
# ============================================================================
@router.get("/validate-token")
def validate_token(current_user: User = Depends(get_current_active_user)):
    """Validasi token aktif"""
    try:
        return success_response(
            data={
                "is_valid": True,
                "username": current_user.username,
                "role_name": current_user.role_name,
                "last_activity": current_user.last_activity
            },
            message="Token masih aktif dan valid"
        )
    except Exception as e:
        logger.error(f"Validate token error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=error_response("Internal server error", 500)
        )
