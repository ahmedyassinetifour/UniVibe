from sqlalchemy import Column, Integer, String, Text, Enum, Date, TIMESTAMP, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from api.database.connection import Base

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
    phone_number = Column(String(15))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    club_memberships = relationship("ClubMember", back_populates="user")
    join_requests = relationship("ClubJoinRequest", back_populates="user")
    bio = Column(String(255))
    about_me = Column(Text)
    interests = Column(JSON)

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
    join_requests = relationship("ClubJoinRequest", back_populates="club")

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

class ClubJoinRequest(Base):
    __tablename__ = 'club_join_requests'
    request_id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey('clubs.club_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    request_message = Column(Text, nullable=True)
    status = Column(Enum('pending', 'approved', 'rejected', name='request_status'), default='pending')
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # Define relationships
    user = relationship("User", back_populates="join_requests")
    club = relationship("Club", back_populates="join_requests")

class EventParticipation(Base):
    __tablename__ = 'event_participation'
    participation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    event_id = Column(Integer, ForeignKey('events.event_id'))
    participation_score = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    # Define relationships
    user = relationship("User")
    event = relationship("Event") 