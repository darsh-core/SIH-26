import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import AppUser, UserProfile, RBACRole
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.core.security import get_password_hash

class UserService:
    
    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> Optional[AppUser]:
        return db.query(AppUser).filter(AppUser.id == user_id).first()
        
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[AppUser]:
        return db.query(AppUser).filter(AppUser.email == email).first()
        
    @staticmethod
    def get_users(
        db: Session, skip: int = 0, limit: int = 10
    ) -> Tuple[List[AppUser], int]:
        query = db.query(AppUser)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total
        
    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> AppUser:
        # Check if email exists
        if UserService.get_user_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_in.email} already exists"
            )
            
        hashed_password = get_password_hash(user_in.password)
        db_user = AppUser(
            email=user_in.email,
            hashed_password=hashed_password,
            organization_id=user_in.organization_id,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
        
    @staticmethod
    def update_user(db: Session, user_id: uuid.UUID, user_in: UserUpdate) -> AppUser:
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
            
        for field, value in update_data.items():
            setattr(db_user, field, value)
            
        db.commit()
        db.refresh(db_user)
        return db_user
        
    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID) -> bool:
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        db.delete(db_user)
        db.commit()
        return True
        
    @staticmethod
    def get_profile(db: Session, user_id: uuid.UUID) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user {user_id} not found"
            )
        return profile
        
    @staticmethod
    def create_or_update_profile(
        db: Session, user_id: uuid.UUID, profile_in: ProfileUpdate
    ) -> UserProfile:
        # Verify user exists
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            # Create
            profile_data = profile_in.model_dump(exclude_unset=True)
            # Default missing fields for creation
            if "first_name" not in profile_data:
                profile_data["first_name"] = "First"
            if "last_name" not in profile_data:
                profile_data["last_name"] = "Last"
            if "designation" not in profile_data:
                profile_data["designation"] = "Employee"
            if "department" not in profile_data:
                profile_data["department"] = "Official"
                
            profile = UserProfile(user_id=user_id, **profile_data)
            db.add(profile)
        else:
            # Update
            update_data = profile_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(profile, field, value)
                
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def add_user_role(db: Session, user_id: uuid.UUID, role_name: str) -> AppUser:
        user = UserService.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        role = db.query(RBACRole).filter_by(name=role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RBAC Role {role_name} not found"
            )
        if role not in user.roles:
            user.roles.append(role)
            db.commit()
            db.refresh(user)
        return user
