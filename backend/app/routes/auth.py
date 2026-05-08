from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import User
from ..auth.auth import hash_password, verify_password, create_token
from ..utils.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(name: str, email: str, password: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    return {"message": "Account created"}

def login(email: str, password: str, db: Session = Depends(get_db)):
@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}