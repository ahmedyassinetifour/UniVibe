from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError
import traceback

from api.database.connection import get_db
from api.models.models import EventParticipation, Event, User
from api.schemas.schemas import (
    EventParticipationCreate, 
    EventParticipationResponse, 
    EventParticipationWithUserResponse,
    EventParticipationWithEventResponse
)
from api.auth.utils import get_current_user

router = APIRouter(
    tags=["event_participation"]
)

@router.post("/event-participation", response_model=EventParticipationResponse)
async def create_event_participation(
    participation_data: EventParticipationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a user as participant to an event"""
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == participation_data.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == participation_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the current user is an admin or adding themselves
    is_admin = current_user.role == 'admin'
    is_self = current_user.user_id == participation_data.user_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add yourself as a participant unless you're an admin"
        )
    
    # Check if the participation record already exists
    existing_participation = db.query(EventParticipation).filter(
        EventParticipation.user_id == participation_data.user_id,
        EventParticipation.event_id == participation_data.event_id
    ).first()
    
    if existing_participation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already participating in this event"
        )
    
    # Create the new participation record
    new_participation = EventParticipation(
        user_id=participation_data.user_id,
        event_id=participation_data.event_id,
        participation_score=participation_data.participation_score
    )
    
    try:
        db.add(new_participation)
        db.commit()
        db.refresh(new_participation)
        return new_participation
    except SQLAlchemyError as e:
        db.rollback()
        error_detail = f"Database error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating participation record: {str(e)}"
        )

@router.get("/events/{event_id}/participants", response_model=List[EventParticipationWithUserResponse])
async def get_event_participants(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all participants for a specific event"""
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    try:
        participants = db.query(EventParticipation).filter(
            EventParticipation.event_id == event_id
        ).all()
        
        return participants
    except SQLAlchemyError as e:
        error_detail = f"Database error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching event participants: {str(e)}"
        )

@router.get("/users/{user_id}/participations", response_model=List[EventParticipationWithEventResponse])
async def get_user_event_participations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all events that a user is participating in"""
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify permissions (admin or self)
    is_admin = current_user.role == 'admin'
    is_self = current_user.user_id == user_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own participations unless you're an admin"
        )
    
    try:
        participations = db.query(EventParticipation).filter(
            EventParticipation.user_id == user_id
        ).all()
        
        return participations
    except SQLAlchemyError as e:
        error_detail = f"Database error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user participations: {str(e)}"
        )

@router.delete("/event-participation/{participation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_participation(
    participation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a participation record"""
    participation = db.query(EventParticipation).filter(
        EventParticipation.participation_id == participation_id
    ).first()
    
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation record not found"
        )
    
    # Check permissions (admin, event owner, or self)
    is_admin = current_user.role == 'admin'
    is_self = current_user.user_id == participation.user_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove your own participation unless you're an admin"
        )
    
    try:
        db.delete(participation)
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        error_detail = f"Database error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting participation record: {str(e)}"
        )

@router.put("/event-participation/{participation_id}/score", response_model=EventParticipationResponse)
async def update_participation_score(
    participation_id: int,
    score: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a participant's participation score"""
    participation = db.query(EventParticipation).filter(
        EventParticipation.participation_id == participation_id
    ).first()
    
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation record not found"
        )
    
    # Only admins can update participation scores
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update participation scores"
        )
    
    try:
        participation.participation_score = score
        db.commit()
        db.refresh(participation)
        return participation
    except SQLAlchemyError as e:
        db.rollback()
        error_detail = f"Database error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating participation score: {str(e)}"
        ) 