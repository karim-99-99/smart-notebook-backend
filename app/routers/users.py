from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import User
from app.auth import hash_password
from app.shemeas import UserRegister

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        hashed = hash_password(user_data.password)
        user = User(email=user_data.email, hashed_password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "User registered successfully", "email": user.email}
    except ValueError as e:
        # Catch password validation errors from hash_password
        db.rollback()
        error_msg = str(e)
        if "72 bytes" in error_msg.lower() or "password cannot be longer" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too long. {error_msg}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password hashing failed: {error_msg}"
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        print(f"Registration error: {error_detail}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {error_detail}"
        )
