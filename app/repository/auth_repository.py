from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from app.domain.models import User, PasswordResetToken, Role 
from app.api.schemas.auth_schema import UserCreate, ProfileUpdateRequest

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user: UserCreate, hashed_password: str) -> User:
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            organization=user.organization 
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_last_activity(self, user_id: int):
        self.db.query(User).filter(User.id == user_id).update(
            {"last_activity": datetime.now(timezone.utc)}
        )
        self.db.commit()

    def update_password(self, user_id: int, new_hashed_password: str):

        self.db.query(User).filter(User.id == user_id).update(
            {"hashed_password": new_hashed_password}
        )
        self.db.commit()

    def increment_token_version(self, user_id: int): 
        self.db.query(User).filter(User.id == user_id).update(
            {"token_version": User.token_version + 1}
        )
        self.db.commit()

    def update_user_profile(self, user_id: int, payload: ProfileUpdateRequest) -> User:
        user = self.get_user_by_id(user_id)
        if user:
            user.username = payload.username
            user.email = payload.email
            user.full_name = payload.full_name
            user.organization = payload.organization
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user

    def change_password(self, user_id: int, new_hashed_password: str):
        self.db.query(User).filter(User.id == user_id).update(
            {
                "hashed_password": new_hashed_password,
                "updated_at": datetime.now(timezone.utc)
            }
        )
        self.db.commit()

    def mark_reset_tokens_used(self, user_id: int):
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None)
        ).update({"used_at": datetime.now(timezone.utc)})
        self.db.commit()

    def create_reset_token(self, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(reset_token)
        self.db.commit()
        self.db.refresh(reset_token)
        return reset_token

    def get_reset_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()

    def mark_token_used(self, token_id: int):
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.id == token_id
        ).update({"used_at": datetime.now(timezone.utc)})
        self.db.commit()

    def update_user_role(self, user_id: int, role_name: str) -> User:
        user = self.get_user_by_id(user_id)
        if user:
            user.role_name = role_name
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user

    def get_all_roles(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.name).all()

    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == role_name).first()

    def verify_user(self, user_id: int, is_verified: bool = True, is_active: bool = True) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if user:
            user.is_verified = is_verified
            user.is_active = is_active
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user

    def reject_user(self, user_id: int) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if user:
            user.is_verified = False
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user
    

    def get_user_by_nip(self, nip: str):
        return self.db.query(User).filter(User.nip == nip).first()

    def create_user_without_password(self, user: UserCreate):
        from app.domain.models import User
        db_user = User(
            nip=user.nip,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            jabatan=user.jabatan,
            organization=user.organization,
            no_telepon=user.no_telepon,
            hashed_password=None,  # Belum ada password
            is_active=False,
            is_verified=False,
            status_verifikasi="pending"
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def approve_user(self, user_id: int, verified_by: int, notes: str = None):
        """Approve user - set is_verified=True, is_active=True"""
        from app.domain.models import User
        from datetime import datetime, timezone
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_verified = True
            user.is_active = True
            user.status_verifikasi = "approved"
            user.verified_by = verified_by
            user.verified_at = datetime.now(timezone.utc)
            user.verification_notes = notes,
            user.role_name = "Eksekutif",
            user.is_approved = True
            self.db.commit()
            self.db.refresh(user)
        return user

    def reject_user(self, user_id: int, verified_by: int, notes: str = None):
        """Reject user - set status_verifikasi=rejected"""
        from app.domain.models import User
        from datetime import datetime, timezone
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.status_verifikasi = "rejected"
            user.verified_by = verified_by
            user.verified_at = datetime.now(timezone.utc)
            user.verification_notes = notes,
            user.is_approved = False
            self.db.commit()
            self.db.refresh(user)
        return user

    def set_user_password(self, user_id: int, hashed_password: str):
        """Set password user pertama kali"""
        from app.domain.models import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.hashed_password = hashed_password
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_set_password_token(self, user_id: int, token_hash: str, expires_at):
        from app.domain.models import PasswordResetToken
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_set_password_token(self, token_hash: str):
        from app.domain.models import PasswordResetToken
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()

    def mark_set_password_token_used(self, token_id: int):
        from app.domain.models import PasswordResetToken
        from datetime import datetime, timezone
        
        token = self.db.query(PasswordResetToken).filter(PasswordResetToken.id == token_id).first()
        if token:
            token.used_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_pending_users(self, limit: int = 50, offset: int = 0):
        from app.domain.models import User
        return self.db.query(User).filter(
            User.status_verifikasi == "pending"
        ).order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    def count_pending_users(self):
        from app.domain.models import User
        return self.db.query(User).filter(User.status_verifikasi == "pending").count()
    
    # ===================MANAGEMENT PENEGGUNA==========================
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all_users(
        self, 
        limit: int = 50, 
        page: int = 0, 
        search: str = None, 
        role_filter: str = None, 
    ):
        from app.domain.models import User
        
        query = self.db.query(User)
        
        # Filter pencarian
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_pattern)) |
                (User.username.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)) |
                (User.nip.ilike(search_pattern)) |
                (User.jabatan.ilike(search_pattern)) |
                (User.organization.ilike(search_pattern)) |
                (User.is_active.ilike(search_pattern))
            )
        
        if role_filter:
            query = query.filter(User.role_name == role_filter)
        

        
        query = query.order_by(User.created_at.desc())
        total = query.count()
        users = query.limit(limit).offset(page).all()
        
        return users, total
    
    def toggle_user_active(self, user_id: int, is_active: bool):
        from app.domain.models import User
        from datetime import datetime, timezone
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = is_active
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user


    def create_user_by_admin(self, user_data: dict, hashed_password: str):
        from app.domain.models import User
        
        db_user = User(
            nip=user_data['nip'],
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            jabatan=user_data['jabatan'],
            organization=user_data['organization'],
            no_telepon=user_data['no_telepon'],
            role_name=user_data['role_name'],
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            status_verifikasi="approved",
            is_approved=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user


    def update_user_by_admin(self, user_id: int, update_data: dict):
        from app.domain.models import User
        from datetime import datetime, timezone
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            # Update hanya field yang diberikan
            for key, value in update_data.items():
                if value is not None:
                    setattr(user, key, value)
            
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user