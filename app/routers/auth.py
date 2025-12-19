from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.auth import verify_password, create_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"error": "Invalid credentials"}
    if not verify_password(password, user.hashed_password):
        return {"error": "Invalid credentials"}
    
    token = create_token({"sub": user.email})
    return {"access_token": token}
