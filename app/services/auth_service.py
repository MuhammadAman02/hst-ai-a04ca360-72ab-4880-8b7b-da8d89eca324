"""Authentication service for user management."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_session, User
from app.core.config import settings


class AuthService:
    """Service for user authentication and management."""
    
    def __init__(self):
        pass
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            salt, password_hash = hashed_password.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False
    
    async def register_user(self, username: str, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """Register a new user."""
        session = get_session()
        try:
            # Check if username already exists
            existing_user = session.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return {"success": False, "message": "Username already exists"}
                else:
                    return {"success": False, "message": "Email already registered"}
            
            # Create new user
            hashed_password = self._hash_password(password)
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )
            
            session.add(user)
            session.commit()
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }
            }
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Registration failed: {str(e)}"}
        finally:
            session.close()
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with username/email and password."""
        session = get_session()
        try:
            # Find user by username or email
            user = session.query(User).filter(
                and_(
                    or_(User.username == username, User.email == username),
                    User.is_active == True
                )
            ).first()
            
            if not user or not self._verify_password(password, user.hashed_password):
                return {"success": False, "message": "Invalid credentials"}
            
            # Update last login (if you want to track this)
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Authentication failed: {str(e)}"}
        finally:
            session.close()
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by ID."""
        session = get_session()
        try:
            user = session.query(User).filter(
                and_(User.id == user_id, User.is_active == True)
            ).first()
            
            if not user:
                return None
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            
        finally:
            session.close()
    
    async def update_user_profile(self, user_id: int, email: str = None, full_name: str = None) -> Dict[str, Any]:
        """Update user profile information."""
        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Check if email is already taken by another user
            if email and email != user.email:
                existing_user = session.query(User).filter(
                    and_(User.email == email, User.id != user_id)
                ).first()
                if existing_user:
                    return {"success": False, "message": "Email already in use"}
                user.email = email
            
            if full_name is not None:
                user.full_name = full_name
            
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }
            }
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Update failed: {str(e)}"}
        finally:
            session.close()
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Verify current password
            if not self._verify_password(current_password, user.hashed_password):
                return {"success": False, "message": "Current password is incorrect"}
            
            # Update password
            user.hashed_password = self._hash_password(new_password)
            user.updated_at = datetime.now()
            session.commit()
            
            return {"success": True, "message": "Password changed successfully"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Password change failed: {str(e)}"}
        finally:
            session.close()
    
    async def create_admin_user(self) -> Dict[str, Any]:
        """Create default admin user if none exists."""
        session = get_session()
        try:
            # Check if admin user already exists
            admin_user = session.query(User).filter(User.is_admin == True).first()
            if admin_user:
                return {"success": False, "message": "Admin user already exists"}
            
            # Create admin user
            admin_password = "admin123"  # Change this in production
            hashed_password = self._hash_password(admin_password)
            
            admin = User(
                username="admin",
                email="admin@casio-watches.com",
                full_name="Administrator",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True
            )
            
            session.add(admin)
            session.commit()
            
            return {
                "success": True,
                "message": "Admin user created successfully",
                "credentials": {
                    "username": "admin",
                    "password": admin_password
                }
            }
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Admin creation failed: {str(e)}"}
        finally:
            session.close()
    
    def is_admin(self, user: Dict[str, Any]) -> bool:
        """Check if user has admin privileges."""
        return user.get("is_admin", False) if user else False
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users (admin only)."""
        session = get_session()
        try:
            users = session.query(User).offset(offset).limit(limit).all()
            
            result = []
            for user in users:
                result.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                })
            
            return result
            
        finally:
            session.close()