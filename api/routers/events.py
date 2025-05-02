from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import traceback

from api.database.connection import get_db
from api.models.models import Event, Club, User, ClubMember
from api.schemas.schemas import EventResponse, EventCreate, EventResponseDebug
from api.auth.utils import get_current_user

router = APIRouter(
    tags=["events"]
)

@router.get("/events", response_model=List[EventResponseDebug])
async def get_events(db: Session = Depends(get_db), 
                   current_user: User = Depends(get_current_user)):
    try:
        events = db.query(Event).all()
        # Check if any events have None in created_at
        for event in events:
            if event.created_at is None:
                print(f"Warning: Event {event.event_id} has None in created_at")
        
        return events
    except Exception as e:
        # Log the error with traceback
        error_detail = f"Error fetching events: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching events: {str(e)}"
        )

@router.get("/events-raw")
async def get_events_raw(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """Fallback endpoint that returns events without model validation"""
    try:
        events = db.query(Event).all()
        # Manually convert to dict to avoid pydantic validation
        result = []
        for event in events:
            event_dict = {
                "event_id": event.event_id,
                "event_name": event.event_name,
                "event_description": event.event_description,
                "event_date": str(event.event_date) if event.event_date else None,
                "event_image": event.event_image,
                "club_id": event.club_id,
                "created_at": str(event.created_at) if event.created_at else None
            }
            result.append(event_dict)
        return {"events": result}
    except Exception as e:
        error_detail = f"Error in raw events: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {"error": str(e), "traceback": str(traceback.format_exc())}

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/events", response_model=EventResponse)
async def create_event(event_data: EventCreate, db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)):
    # Ensure the club exists
    club = db.query(Club).filter(Club.club_id == event_data.club_id).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Check if user is an admin
    is_admin = current_user.role == 'admin'
    
    # Check if user is the club leader
    is_club_leader = club.leader_id == current_user.user_id
    
    # Check if user is a member of the club
    is_club_member = db.query(ClubMember).filter(
        ClubMember.club_id == event_data.club_id,
        ClubMember.user_id == current_user.user_id
    ).first() is not None
    
    # Only allow admins, club leaders, or club members to create events
    if not (is_admin or is_club_leader or is_club_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a club member, club leader, or admin to create an event for this club"
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