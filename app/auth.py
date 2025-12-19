from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Initialize CryptContext with error handling
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"Warning: Error initializing CryptContext: {e}")
    pwd_context = None

def hash_password(pwd: str):
    # Ensure password is a string and check length
    if not isinstance(pwd, str):
        raise ValueError("Password must be a string")
    
    pwd_bytes = pwd.encode('utf-8')
    password_length = len(pwd_bytes)
    
    print(f"DEBUG hash_password: password={repr(pwd)}, length={password_length} bytes")
    
    if password_length > 72:
        raise ValueError(f"Password cannot be longer than 72 bytes (got {password_length} bytes)")
    
    # Try using passlib first
    try:
        if pwd_context:
            result = pwd_context.hash(pwd)
            print(f"DEBUG: Successfully hashed password using passlib")
            return result
    except ValueError as e:
        # Re-raise ValueError as-is (these are our validation errors)
        raise
    except Exception as e:
        print(f"Warning: passlib hash failed: {type(e).__name__}: {e}, trying bcrypt directly")
        import traceback
        traceback.print_exc()
    
    # Fallback to bcrypt directly
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        result = hashed.decode('utf-8')
        print(f"DEBUG: Successfully hashed password using bcrypt directly")
        return result
    except ValueError as e:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        print(f"ERROR: bcrypt direct hash failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Password hashing failed: {str(e)}")

def verify_password(plain, hashed):
    # Try using passlib first, fallback to bcrypt directly if needed
    try:
        if pwd_context:
            return pwd_context.verify(plain, hashed)
    except Exception:
        pass
    
    # Fallback to bcrypt directly
    try:
        plain_bytes = plain.encode('utf-8') if isinstance(plain, str) else plain
        hashed_bytes = hashed.encode('utf-8') if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification failed: {e}")
        return False

def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
