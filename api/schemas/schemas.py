from pydantic import BaseModel, validator
from datetime import datetime, date
from typing import List, Optional, Literal, Union, Any

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Literal['student', 'club_leader', 'admin']
    first_name: str
    last_name: str
    date_of_birth: date
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    about_me: Optional[str] = None
    interests: Optional[List[str]] = None

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str
    date_of_birth: date
    created_at: Optional[datetime] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    about_me: Optional[str] = None
    interests: Optional[List[Any]] = None

    class Config:
        from_attributes = True
        
    @validator('created_at', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try parsing with multiple formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value

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
         
    @validator('created_at', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try parsing with multiple formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value

# Join Request Schemas
class JoinRequestCreate(BaseModel):
    request_message: Optional[str] = None

class JoinRequestResponse(BaseModel):
    request_id: int
    club_id: int
    user_id: int
    request_message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return datetime.now()  # Provide default for required fields
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try parsing with multiple formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value

class JoinRequestWithUserResponse(BaseModel):
    request_id: int
    club_id: int
    user_id: int
    request_message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True

class JoinRequestWithClubResponse(BaseModel):
    request_id: int
    club_id: int
    user_id: int
    request_message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    club: ClubResponse

    class Config:
        from_attributes = True

class JoinRequestAction(BaseModel):
    action: Literal['approve', 'reject']

class EventCreate(BaseModel):
    event_name: str
    event_description: Optional[str] = None
    event_date: date
    event_image: Optional[str] = None
    club_id: int

# Debug version that allows for more flexible date handling
class EventResponseDebug(BaseModel):
    event_id: int
    event_name: str
    event_description: Optional[str] = None
    event_date: Union[date, str, None]
    event_image: Optional[str] = None
    club_id: int
    created_at: Union[datetime, str, None]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @validator('event_date', 'created_at', pre=True)
    def parse_dates(cls, value):
        if isinstance(value, str):
            return value
        return value

class EventResponse(BaseModel):
    event_id: int
    event_name: str
    event_description: Optional[str] = None
    event_date: date
    event_image: Optional[str] = None
    club_id: int
    created_at: Optional[datetime] = None

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

class RoleAssignRequest(BaseModel):
    user_id: int
    role: Literal['student', 'club_leader', 'admin']

# Schema for updating user profile picture
class ProfilePictureUpdate(BaseModel):
    profile_picture: str

# Schema for updating user profile information
class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    about_me: Optional[str] = None
    phone_number: Optional[str] = None
    interests: Optional[List[Any]] = None

# Event Participation Schemas
class EventParticipationCreate(BaseModel):
    user_id: int
    event_id: int
    participation_score: Optional[int] = 0

class EventParticipationResponse(BaseModel):
    participation_id: int
    user_id: int
    event_id: int
    participation_score: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @validator('created_at', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try parsing with multiple formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value

class EventParticipationWithUserResponse(BaseModel):
    participation_id: int
    user_id: int
    event_id: int
    participation_score: int
    created_at: Optional[datetime] = None
    user: UserResponse
    
    class Config:
        from_attributes = True

class EventParticipationWithEventResponse(BaseModel):
    participation_id: int
    user_id: int
    event_id: int
    participation_score: int
    created_at: Optional[datetime] = None
    event: EventResponse
    
    class Config:
        from_attributes = True 