# Event Participation Schemas
class EventParticipationCreate(BaseModel):
    pass  # No need for additional data, user_id comes from current_user and event_id from path

class EventParticipationResponse(BaseModel):
    participation_id: int
    user_id: int
    event_id: int
    participation_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EventParticipationWithUserResponse(EventParticipationResponse):
    user: UserResponse

    class Config:
        from_attributes = True

# Scores Schemas
class ScoreCreate(BaseModel):
    user_id: int
    score_value: int

class ScoreResponse(BaseModel):
    score_id: int
    user_id: int
    score_value: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ScoreWithUserResponse(ScoreResponse):
    user: UserResponse

    class Config:
        from_attributes = True

# Register for an event
@app.post("/events/{event_id}/participate", response_model=EventParticipationResponse)
async def participate_in_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already participating
    existing_participation = db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id,
        EventParticipation.user_id == current_user.user_id
    ).first()
    
    if existing_participation:
        raise HTTPException(status_code=400, detail="Already registered for this event")
    
    # Create new participation record
    new_participation = EventParticipation(
        event_id=event_id,
        user_id=current_user.user_id,
        participation_score=None  # Will be updated after the event
    )
    
    db.add(new_participation)
    db.commit()
    db.refresh(new_participation)
    
    return new_participation

# Get all participants for an event
@app.get("/events/{event_id}/participants", response_model=List[EventParticipationWithUserResponse])
async def get_event_participants(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get all participants with user data
    participants = db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id
    ).options(
        joinedload(EventParticipation.user)
    ).all()
    
    return participants

# Cancel event participation
@app.delete("/events/{event_id}/participation", status_code=204)
async def cancel_event_participation(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if participating
    participation = db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id,
        EventParticipation.user_id == current_user.user_id
    ).first()
    
    if not participation:
        raise HTTPException(status_code=404, detail="Not registered for this event")
    
    # Delete participation record
    db.delete(participation)
    db.commit()
    
    return None

# Add scores for event participants (club leader only)
@app.post("/events/{event_id}/scores", response_model=ScoreResponse)
async def add_event_score(
    event_id: int,
    score_data: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == event.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or admin
    if club.leader_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only club leader or admin can add scores")
    
    # Check if user is a participant
    participant = db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id,
        EventParticipation.user_id == score_data.user_id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=404, detail="User is not a participant in this event")
    
    # Check if score already exists
    existing_score = db.query(Score).filter(
        Score.event_id == event_id,
        Score.user_id == score_data.user_id
    ).first()
    
    if existing_score:
        raise HTTPException(status_code=400, detail="Score already exists for this user and event")
    
    # Create new score
    new_score = Score(
        event_id=event_id,
        user_id=score_data.user_id,
        score_value=score_data.score_value
    )
    
    # Also update participation score
    participant.participation_score = score_data.score_value
    
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    
    # Create notification for the user
    notification = Notification(
        user_id=score_data.user_id,
        notification_type="score",
        reference_id=new_score.score_id,
        notification_text=f"You received a score of {score_data.score_value} for event '{event.event_name}'",
        is_read=False,
        notification_date=datetime.now()
    )
    
    db.add(notification)
    db.commit()
    
    return new_score

# Get all scores for an event
@app.get("/events/{event_id}/scores", response_model=List[ScoreWithUserResponse])
async def get_event_scores(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if event exists
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get all scores with user data
    scores = db.query(Score).filter(
        Score.event_id == event_id
    ).options(
        joinedload(Score.user)
    ).all()
    
    return scores

# Get current user's scores
@app.get("/users/me/scores", response_model=List[ScoreResponse])
async def get_my_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):