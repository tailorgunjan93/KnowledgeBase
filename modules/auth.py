"""Authentication module for user management."""
import bcrypt
from typing import Optional, Dict
from database.db_manager import DatabaseManager


class Auth:
    """Handles user authentication and registration."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize authentication with database manager."""
        self.db = db_manager
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
        
        Returns:
            User ID if successful, None if username/email already exists
        """
        # Validate inputs
        if not username or not email or not password:
            return None
        
        if len(password) < 6:
            return None
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user in database
        user_id = self.db.create_user(username, email, password_hash)
        return user_id
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User dict if authentication successful, None otherwise
        """
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return None
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return None
        
        # Remove password hash from returned user dict
        user_data = dict(user)
        del user_data['password_hash']
        
        return user_data
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID."""
        user = self.db.get_user_by_id(user_id)
        
        if not user:
            return None
        
        # Remove password hash
        user_data = dict(user)
        del user_data['password_hash']
        
        return user_data
