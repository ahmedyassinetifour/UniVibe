# Update User Schema
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture: Optional[str] = None

# Update Club Schema
class ClubUpdate(BaseModel):
    club_name: Optional[str] = None
    description: Optional[str] = None
    pic: Optional[str] = None

# Update Event Schema
class EventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_description: Optional[str] = None
    event_date: Optional[date] = None
    event_image: Optional[str] = None

# Update user profile
@app.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Update user fields that are provided
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    current_user.updated_at = datetime.now()
    db.commit()
    db.refresh(current_user)
    
    return current_user

# Update club details (club leader only)
@app.put("/clubs/{club_id}", response_model=ClubResponse)
async def update_club(
    club_id: int,
    club_data: ClubUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the club
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or admin
    if club.leader_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only club leader or admin can update club details")
    
    # Update club fields that are provided
    for key, value in club_data.dict(exclude_unset=True).items():
        setattr(club, key, value)
    
    db.commit()
    db.refresh(club)
    
    return club

# Update event details (club leader only)
@app.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the event
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == event.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or admin
    if club.leader_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only club leader or admin can update event details")
    
    # Update event fields that are provided
    for key, value in event_data.dict(exclude_unset=True).items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    
    return event

# Delete a club (club leader or admin only)
@app.delete("/clubs/{club_id}", status_code=204)
async def delete_club(
    club_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the club
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or admin
    if club.leader_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only club leader or admin can delete the club")
    
    # Delete the club (cascade will handle related records)
    db.delete(club)
    db.commit()
    
    return None

# Delete an event (club leader or admin only)
@app.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the event
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == event.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or admin
    if club.leader_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only club leader or admin can delete the event")
    
    # Delete the event
    db.delete(event)
    db.commit()
    
    return None