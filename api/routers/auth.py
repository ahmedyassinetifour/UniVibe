from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.models.models import User
from api.schemas.schemas import UserCreate, UserResponse, LoginCredentials, TokenRequest
from api.auth.utils import get_password_hash, verify_password, generate_token

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/signup")
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | 
        (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    hashed_password = get_password_hash(user_data.password)
    auth_token = generate_token()
    
    new_user = User(
        **user_data.dict(exclude={'password'}), 
        password_hash=hashed_password, 
        auth_token=auth_token
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return both the message and the user_id
    return {
        "message": f"Account created successfully for {user_data.first_name} {user_data.last_name}",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "email": new_user.email
    }

@router.post("/login")
async def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    new_token = generate_token()
    user.auth_token = new_token
    db.commit()
    return {"auth_token": new_token}

@router.post("/verify-token")
async def verify_token(request: TokenRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.auth_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"valid": True, "username": user.username} 