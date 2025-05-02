from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional, Literal
from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, Date, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
import secrets
from passlib.context import CryptContext

# Database setup
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:45151515@localhost/univibe2"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    auth_token = Column(String(255))
    profile_picture = Column(Text)
    role = Column(Enum('student', 'club_leader', 'admin', name='user_role'))
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    club_memberships = relationship("ClubMember", back_populates="user")

class Club(Base):
    __tablename__ = 'clubs'
    club_id = Column(Integer, primary_key=True, index=True)
    club_name = Column(String(100))
    description = Column(Text)
    pic = Column(Text)
    leader_id = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    leader = relationship("User")
    members = relationship("ClubMember", back_populates="club")

class Event(Base):
    __tablename__ = 'events'
    event_id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(100))
    event_description = Column(Text)
    event_date = Column(Date)
    event_image = Column(Text)
    club_id = Column(Integer, ForeignKey('clubs.club_id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    club = relationship("Club")

class ClubMember(Base):
    __tablename__ = 'club_members'
    club_id = Column(Integer, ForeignKey('clubs.club_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    joined_at = Column(TIMESTAMP, default=datetime.now)
    
    # Define relationships
    user = relationship("User", back_populates="club_memberships")
    club = relationship("Club", back_populates="members")

Base.metadata.create_all(bind=engine)

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Literal['student', 'club_leader', 'admin']
    first_name: str
    last_name: str
    date_of_birth: date

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str
    date_of_birth: date
    created_at: datetime

    class Config:
        from_attributes = True 

class ClubCreate(BaseModel):
    club_name: str
    description: Optional[str] = None
    pic: Optional[str] = None
    leader_id: int

class ClubResponse(BaseModel):
    club_id: int
    club_name: str
    description: Optional[str] = None
    pic: Optional[str] = None
    leader_id: int
    created_at: Optional[datetime] = None

    class Config:
         from_attributes = True

class EventCreate(BaseModel):
    event_name: str
    event_description: Optional[str] = None
    event_date: date
    event_image: Optional[str] = None
    club_id: int

class EventResponse(BaseModel):
    event_id: int
    event_name: str
    event_description: Optional[str] = None
    event_date: date
    event_image: Optional[str] = None
    club_id: int
    created_at: datetime

    class Config:
         from_attributes = True

class TokenRequest(BaseModel):
    token: str

class LoginCredentials(BaseModel):
    username: str
    password: str

class ClubMemberResponse(BaseModel):
    user_id: int
    joined_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ClubMemberWithUserResponse(BaseModel):
    user_id: int
    joined_at: Optional[datetime] = None
    user: UserResponse
    
    class Config:
        from_attributes = True

class ClubMemberWithClubResponse(BaseModel):
    club_id: int
    joined_at: Optional[datetime] = None
    club: ClubResponse
    
    class Config:
        from_attributes = True

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Auth endpoints
@app.post("/auth/signup", response_model=UserResponse)
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
    auth_token = secrets.token_urlsafe(32)
    
    new_user = User(
        **user_data.dict(exclude={'password'}), 
        password_hash=hashed_password, 
        auth_token=auth_token
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login")
async def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    new_token = secrets.token_urlsafe(32)
    user.auth_token = new_token
    db.commit()
    return {"auth_token": new_token}

@app.post("/auth/verify-token")
async def verify_token(request: TokenRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.auth_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"valid": True, "username": user.username}

# Protected routes
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.auth_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/students", response_model=List[UserResponse])
async def get_students(db: Session = Depends(get_db), 
                      current_user: User = Depends(get_current_user)):
    return db.query(User).filter(User.role == 'student').all()

@app.get("/clubs", response_model=List[ClubResponse])
async def get_clubs(db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    return db.query(Club).all()

@app.get("/clubs/{club_id}", response_model=ClubResponse)
async def get_club(club_id: int, db: Session = Depends(get_db), 
                 current_user: User = Depends(get_current_user)):
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@app.get("/events", response_model=List[EventResponse])
async def get_events(db: Session = Depends(get_db), 
                   current_user: User = Depends(get_current_user)):
    return db.query(Event).all()

@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Admin role assignment endpoint
class RoleAssignRequest(BaseModel):
    user_id: int
    role: Literal['student', 'club_leader', 'admin']

@app.post("/admin/assign_role")
async def assign_role_to_user(request: RoleAssignRequest, 
                              db: Session = Depends(get_db), 
                              current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can assign roles.")
    
    user_to_update = db.query(User).filter(User.user_id == request.user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_to_update.role = request.role
    db.commit()
    db.refresh(user_to_update)
    return user_to_update

# Create Club Endpoint
@app.post("/clubs", response_model=ClubResponse)
async def create_club(club_data: ClubCreate, db: Session = Depends(get_db), 
                      current_user: User = Depends(get_current_user)):
    # Ensure the leader exists and is a club_leader
    leader = db.query(User).filter(User.user_id == club_data.leader_id, User.role == 'club_leader').first()
    if not leader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leader not found or not authorized"
        )
    
    # Create the new club
    new_club = Club(
        club_name=club_data.club_name,
        description=club_data.description,
        pic=club_data.pic,
        leader_id=club_data.leader_id
    )
    
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    return new_club

# Create Event Endpoint
@app.post("/events", response_model=EventResponse)
async def create_event(event_data: EventCreate, db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)):
    # Ensure the club exists
    club = db.query(Club).filter(Club.club_id == event_data.club_id).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Create the new event
    new_event = Event(
        event_name=event_data.event_name,
        event_description=event_data.event_description,
        event_date=event_data.event_date,
        event_image=event_data.event_image,
        club_id=event_data.club_id
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# Get all members of a club
@app.get("/clubs/{club_id}/members", response_model=List[ClubMemberWithUserResponse])
async def get_club_members(club_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    # Check if club exists
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Get all members of the club with their user data
    club_members = db.query(ClubMember).filter(
        ClubMember.club_id == club_id
    ).options(
        joinedload(ClubMember.user)
    ).all()
    
    return club_members

# Get all clubs a student is in
@app.get("/users/{user_id}/clubs", response_model=List[ClubMemberWithClubResponse])
async def get_user_clubs(user_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all clubs the user is a member of with club data
    user_clubs = db.query(ClubMember).filter(
        ClubMember.user_id == user_id
    ).options(
        joinedload(ClubMember.club)
    ).all()
    
    return user_clubs

# Get all clubs the current user is in
@app.get("/users/me/clubs", response_model=List[ClubMemberWithClubResponse])
async def get_my_clubs(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    # Get all clubs the current user is a member of with club data
    user_clubs = db.query(ClubMember).filter(
        ClubMember.user_id == current_user.user_id
    ).options(
        joinedload(ClubMember.club)
    ).all()
    
    return user_clubs

# Join a club
@app.post("/clubs/{club_id}/join", response_model=ClubMemberResponse)
async def join_club(club_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    # Check if club exists
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if already a member
    existing_membership = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.user_id == current_user.user_id
    ).first()
    
    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this club")
    
    # Create new membership
    new_membership = ClubMember(
        club_id=club_id,
        user_id=current_user.user_id
    )
    
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    return new_membership

# Leave a club
@app.delete("/clubs/{club_id}/leave", status_code=204)
async def leave_club(club_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    # Check if club exists
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if a member
    membership = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.user_id == current_user.user_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this club")
    
    # Delete membership
    db.delete(membership)
    db.commit()
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
