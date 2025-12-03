from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repository.auth_repository import AuthRepository
from app.api.schemas.auth_schema import(
    UserCreate, UserLogin,
    ProfileUpdateRequest, ChangePasswordRequest, 
    ForgotPasswordRequest, ResetPasswordRequest,
    AdminUserCreate, AdminUserUpdate
)
from datetime import timedelta, datetime, timezone 
from app.config import settings
from app.utils.auth_util import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.utils.email_util import (
    send_reset_password_email,
    send_registration_confirmation_email,
    send_set_password_email,
    send_password_changed_notification
)
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    ALLOWED_ROLES = ["Super Admin", "Eksekutif"]
    DEFAULT_ROLE_AFTER_APPROVAL = "Eksekutif"
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
    SET_PASSWORD_TOKEN_EXPIRY_HOURS = 24
    
    def __init__(self, db: Session):
        self.repository = AuthRepository(db)

    def _validate_user_exists_by_nip(self, nip: str):
        existing_nip = self.repository.get_user_by_nip(nip)
        if existing_nip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NIP sudah terdaftar"
            )
    
    def _validate_user_exists_by_username(self, username: str):
        existing_user = self.repository.get_user_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username sudah terdaftar"
            )
    
    def _validate_user_exists_by_email(self, email: str):
        existing_email = self.repository.get_user_by_email(email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email sudah terdaftar"
            )

    def _validate_user_status(self, user):
        if not user.is_active:
            logger.error(f"User {user.id} tidak aktif")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pengguna tidak aktif"
            )

        if not user.is_verified:
            logger.error(f"User {user.id} belum terverifikasi")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun Anda masih menunggu persetujuan administrator"
            )
        
        if not user.role_name or user.role_name not in self.ALLOWED_ROLES:
            logger.error(f"Role tidak diizinkan untuk user {user.id}: {user.role_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Hanya {' atau '.join(self.ALLOWED_ROLES)} yang dapat login."
            )

    def _create_token_hash(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def _generate_access_token(self, user) -> dict:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "ver": user.token_version
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "user": user,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES
        }

    def register_user(self, user: UserCreate):
        """Registrasi user baru tanpa password"""
        logger.info(f"Memulai registrasi user: {user.email}")
        
        self._validate_user_exists_by_nip(user.nip)
        self._validate_user_exists_by_username(user.username)
        self._validate_user_exists_by_email(user.email)
        
        new_user = self.repository.create_user_without_password(user)
        logger.info(f"User berhasil dibuat dengan id: {new_user.id}")
        
        try:
            send_registration_confirmation_email(
                email=new_user.email,
                user_display_name=new_user.full_name
            )
            logger.info(f"Email konfirmasi registrasi terkirim ke: {new_user.email}")
        except Exception as e:
            logger.warning(f"Gagal mengirim email konfirmasi registrasi: {str(e)}")
        
        try:
            from app.utils.email_util import send_admin_notification_new_registration
            
            user_data = {
                'nip': new_user.nip,
                'username': new_user.username,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'jabatan': new_user.jabatan,
                'organization': new_user.organization,
                'no_telepon': new_user.no_telepon,
                'created_at': new_user.created_at.strftime('%d %B %Y, %H:%M WIB') if new_user.created_at else '-'
            }
            
            send_admin_notification_new_registration(user_data)
            logger.info(f"Notifikasi admin terkirim ke: {settings.ADMIN_NOTIFICATION_EMAIL}")
        except Exception as e:
            logger.warning(f"Gagal mengirim notifikasi ke admin: {str(e)}")
        
        return new_user

    def authenticate_user(self, login: UserLogin):     
        clean_email = login.email.strip().lower()
        
        user = self.repository.get_user_by_email(clean_email)
        
        if not user:
            logger.error(f"User dengan email '{clean_email}' tidak ditemukan")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pastikan email atau kata sandi yang Anda masukkan sudah sesuai"
            )
                
        if not user.hashed_password:
            logger.error(f"User {user.id} tidak memiliki password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Akun tidak valid. Silakan hubungi administrator."
            )
        
        if not verify_password(login.password, user.hashed_password):
            logger.error(f"Password tidak sesuai untuk user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pastikan email atau kata sandi yang Anda masukkan sudah sesuai"
            )
        
        self._validate_user_status(user)
        
        self.repository.update_last_activity(user.id)
        
        logger.info(f"Login berhasil untuk user: {user.username}")
        return self._generate_access_token(user)

    def logout_user(self, user):
        logger.info(f"User {user.id} melakukan logout")
        self.repository.increment_token_version(user.id)

    def update_user_profile(self, user, payload: ProfileUpdateRequest):
        """Update profil user"""
        logger.info(f"Update profil untuk user {user.id}")
        
        if payload.username != user.username:
            existing = self.repository.get_user_by_username(payload.username)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username sudah digunakan oleh akun lain"
                )
        
        if payload.email != user.email:
            existing = self.repository.get_user_by_email(payload.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email sudah digunakan oleh akun lain"
                )
        
        return self.repository.update_user_profile(user.id, payload)

    def change_user_password(self, user, payload: ChangePasswordRequest):
        logger.info(f"Ubah password untuk user {user.id}")
        
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password saat ini tidak sesuai"
            )
        
        new_hashed = get_password_hash(payload.new_password)
        
        self.repository.change_password(user.id, new_hashed)
        
        self.repository.increment_token_version(user.id)
        
        try:
            send_password_changed_notification(
                email=user.email,
                user_display_name=user.full_name
            )
            logger.info(f"Notifikasi perubahan password terkirim ke {user.email}")
        except Exception as e:
            logger.warning(f"Gagal mengirim notifikasi perubahan password: {str(e)}")

    def request_password_reset(self, payload: ForgotPasswordRequest) -> bool:
        logger.info(f"Request reset password untuk email: {payload.email}")
        
        user = self.repository.get_user_by_email(payload.email)
        
        if not user or not user.is_verified:
            logger.warning(f"Reset password request untuk email tidak valid: {payload.email}")
            return False
        
        is_admin = user.role_name == "Super Admin"
        
        self.repository.mark_reset_tokens_used(user.id)
        
        raw_token = secrets.token_urlsafe(48)
        token_hash = self._create_token_hash(raw_token)
        
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.PASSWORD_RESET_TOKEN_EXPIRY_HOURS
        )
        
        self.repository.create_reset_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        # Kirim email
        try:
            send_reset_password_email(user.email, raw_token)
            logger.info(f"Email reset password terkirim ke: {user.email}")
        except Exception as e:
            logger.error(f"Gagal mengirim email reset password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal mengirim email reset password"
            )
        
        return is_admin

    def reset_password(self, payload: ResetPasswordRequest):
        logger.info("Memproses reset password")
        
        token_hash = self._create_token_hash(payload.token)
        reset_token = self.repository.get_reset_token(token_hash)
        
        # Validasi token
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token reset password tidak valid"
            )
        
        if reset_token.used_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token sudah pernah digunakan"
            )
        
        if reset_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token sudah kadaluarsa"
            )
        
        new_hashed = get_password_hash(payload.new_password)
        self.repository.change_password(reset_token.user_id, new_hashed)
        
        self.repository.mark_token_used(reset_token.id)
        
        self.repository.increment_token_version(reset_token.user_id)
        
        logger.info(f"Password berhasil direset untuk user {reset_token.user_id}")

    def change_user_role(self, acting_user, target_user_id: int, role_name: str):
        """Ubah role user - Super Admin only"""
        if acting_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Super Admin yang dapat mengubah role user"
            )
        
        target_user = self.repository.get_user_by_id(target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan"
            )
        
        logger.info(f"Admin {acting_user.id} mengubah role user {target_user_id} menjadi {role_name}")
        return self.repository.update_user_role(target_user_id, role_name)

    def list_roles(self):
        """List semua role yang tersedia"""
        return self.repository.get_all_roles()

    def get_pending_users_for_verification(self, limit: int = 50, offset: int = 0):
        """Dapatkan daftar user yang menunggu verifikasi"""
        users = self.repository.get_pending_users(limit, offset)
        total = self.repository.count_pending_users()
        return users, total
    
    def verify_user(self, current_user, user_id: int, payload):
        """Verifikasi user - approve atau reject"""
        logger.info(f"Admin {current_user.id} memverifikasi user {user_id}: {payload.status}")
        
        target_user = self.repository.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan"
            )
        
        if target_user.status_verifikasi != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User sudah {target_user.status_verifikasi}"
            )
        
        if payload.status == "approve":
            return self._approve_user(target_user, current_user.id, payload.notes)
        
        elif payload.status == "reject":
            return self._reject_user(target_user, current_user.id, payload.notes)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status harus 'approve' atau 'reject'"
            )

    def _approve_user(self, target_user, admin_id: int, notes: str):
        approved_user = self.repository.approve_user(
            user_id=target_user.id,
            verified_by=admin_id,
            notes=notes
        )
        
        raw_token = secrets.token_urlsafe(48)
        token_hash = self._create_token_hash(raw_token)
        
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.SET_PASSWORD_TOKEN_EXPIRY_HOURS
        )
        
        self.repository.create_set_password_token(
            user_id=target_user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        try:
            send_set_password_email(
                email=approved_user.email,
                set_password_token=raw_token,
                user_display_name=approved_user.full_name
            )
            logger.info(f"Email set password terkirim ke: {approved_user.email}")
        except Exception as e:
            logger.error(f"Gagal mengirim email set password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal mengirim email set password"
            )
        
        return approved_user

    def _reject_user(self, target_user, admin_id: int, notes: str):
        from app.utils.email_util import send_registration_rejection_email
        
        rejected_user = self.repository.reject_user(
            user_id=target_user.id,
            verified_by=admin_id,
            notes=notes
        )
        logger.info(f"User {target_user.id} ditolak oleh admin {admin_id}")
        
        try:
            send_registration_rejection_email(
                email=rejected_user.email,
                user_display_name=rejected_user.full_name,
                rejection_notes=notes
            )
            logger.info(f"Email rejection notification terkirim ke: {rejected_user.email}")
        except Exception as e:
            logger.error(f"Gagal mengirim email rejection notification: {str(e)}")
        
        return rejected_user

    def set_password_from_token(self, payload):
        logger.info("Memproses set password dari token")
        
        token_hash = self._create_token_hash(payload.token)
        token_record = self.repository.get_set_password_token(token_hash)
        
        # Validasi token
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token tidak valid"
            )
        
        if token_record.used_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token sudah pernah digunakan"
            )
        
        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sudah kadaluarsa"
            )
        
        hashed_password = get_password_hash(payload.password)
        self.repository.set_user_password(token_record.user_id, hashed_password)
    
        self.repository.mark_set_password_token_used(token_record.id)
    
        logger.info(f"Password berhasil di-set untuk user {token_record.user_id}")

    
    # ===================MANAGEMENT PENEGGUNA==========================
    
    def get_all_users(
        self, 
        limit: int = 50, 
        page: int = 0, 
        search: str = None, 
        role_filter: str = None
    ):
        
        users, total = self.repository.get_all_users(
            limit=limit,
            page=page,
            search=search,
            role_filter=role_filter
        )
        
        return users, total
    
    def get_user_by_id(self, user_id: int):
        logger.info(f"Mengambil detail user dengan ID: {user_id}")
        
        user = self.repository.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan"
            )
        
        return user

    def toggle_user_active(self, admin_user, user_id: int, is_active: bool):
        if admin_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Super Admin yang dapat mengubah status user"
            )
        
        target_user = self.repository.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan"
            )
        
        if target_user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat mengubah status akun Anda sendiri"
            )
        
        action = "diaktifkan" if is_active else "dinonaktifkan"
        logger.info(f"Admin {admin_user.id} mengubah status user {user_id} menjadi: {action}")
        
        updated_user = self.repository.toggle_user_active(user_id, is_active)
        
        # ✨ Jika dinonaktifkan, increment token version untuk force logout
        if not is_active:
            self.repository.increment_token_version(user_id)
            logger.info(f"Token version user {user_id} di-increment (force logout)")
        
        return updated_user


    def create_user_by_admin(self, admin_user, user_data: 'AdminUserCreate'):
        if admin_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Super Admin yang dapat membuat user"
            )
        
        logger.info(f"Admin {admin_user.id} membuat user baru: {user_data.email}")
        
        self._validate_user_exists_by_nip(user_data.nip)
        self._validate_user_exists_by_username(user_data.username)
        self._validate_user_exists_by_email(user_data.email)
        
        hashed_password = get_password_hash(user_data.password)
        
        new_user = self.repository.create_user_by_admin(
            user_data=user_data.dict(exclude={'password'}),
            hashed_password=hashed_password
        )
        
        logger.info(f"User berhasil dibuat oleh admin dengan id: {new_user.id}")
        
        try:
            from app.utils.email_util import send_account_created_by_admin_email
            send_account_created_by_admin_email(
                email=new_user.email,
                user_display_name=new_user.full_name,
                username=new_user.username,
                temporary_password=user_data.password  # ✨ Kirim password temporary
            )
            logger.info(f"Email notifikasi akun terkirim ke: {new_user.email}")
        except Exception as e:
            logger.warning(f"Gagal mengirim email notifikasi: {str(e)}")
        
        return new_user

    def update_user_by_admin(self, admin_user, user_id: int, update_data: 'AdminUserUpdate'):
        if admin_user.role_name != "Super Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Super Admin yang dapat mengubah data user"
            )
        
        target_user = self.repository.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan"
            )
        
        logger.info(f"Admin {admin_user.id} mengupdate user {user_id}")
        
        if update_data.username and update_data.username != target_user.username:
            existing = self.repository.get_user_by_username(update_data.username)
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username sudah digunakan oleh akun lain"
                )
        
        if update_data.email and update_data.email != target_user.email:
            existing = self.repository.get_user_by_email(update_data.email)
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email sudah digunakan oleh akun lain"
                )
        
        if update_data.nip and update_data.nip != target_user.nip:
            existing = self.repository.get_user_by_nip(update_data.nip)
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="NIP sudah digunakan oleh akun lain"
                )
        
        update_dict = update_data.dict(exclude_none=True)
        updated_user = self.repository.update_user_by_admin(user_id, update_dict)
        
        logger.info(f"User {user_id} berhasil diupdate oleh admin {admin_user.id}")
        return updated_user