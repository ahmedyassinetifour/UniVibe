# Club Join Requests Schema
class ClubJoinRequestCreate(BaseModel):
    request_message: Optional[str] = None

class ClubJoinRequestResponse(BaseModel):
    request_id: int
    club_id: int
    user_id: int
    request_message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClubJoinRequestWithUserResponse(ClubJoinRequestResponse):
    user: UserResponse

    class Config:
        from_attributes = True

# Request to join a club
@app.post("/clubs/{club_id}/request-join", response_model=ClubJoinRequestResponse)
async def request_to_join_club(
    club_id: int, 
    request_data: ClubJoinRequestCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    
    # Check if already requested
    existing_request = db.query(ClubJoinRequest).filter(
        ClubJoinRequest.club_id == club_id,
        ClubJoinRequest.user_id == current_user.user_id,
        ClubJoinRequest.status == 'pending'
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Already requested to join this club")
    
    # Create new join request
    new_request = ClubJoinRequest(
        club_id=club_id,
        user_id=current_user.user_id,
        request_message=request_data.request_message,
        status="pending"
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Create notification for club leader
    notification = Notification(
        user_id=club.leader_id,
        notification_type="join_request",
        reference_id=new_request.request_id,
        notification_text=f"{current_user.username} has requested to join {club.club_name}",
        is_read=False,
        notification_date=datetime.now()
    )
    
    db.add(notification)
    db.commit()
    
    return new_request

# Get all join requests for a club (club leader only)
@app.get("/clubs/{club_id}/join-requests", response_model=List[ClubJoinRequestWithUserResponse])
async def get_club_join_requests(
    club_id: int, 
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if club exists
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or an admin
    is_club_leader = club.leader_id == current_user.user_id
    is_admin = current_user.role == 'admin'
    
    if not (is_club_leader or is_admin):
        raise HTTPException(
            status_code=403, 
            detail="Only club leader or admin can view join requests"
        )
    
    # Create base query
    query = db.query(ClubJoinRequest).filter(ClubJoinRequest.club_id == club_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(ClubJoinRequest.status == status)
    
    # Get requests with user data
    requests = query.options(joinedload(ClubJoinRequest.user)).all()
    
    return requests

# Get all join requests for current user
@app.get("/users/me/join-requests", response_model=List[ClubJoinRequestResponse])
async def get_my_join_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create base query
    query = db.query(ClubJoinRequest).filter(ClubJoinRequest.user_id == current_user.user_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(ClubJoinRequest.status == status)
    
    # Get requests
    requests = query.all()
    
    return requests

# Approve a join request (club leader only)
@app.put("/clubs/join-requests/{request_id}/approve", response_model=ClubJoinRequestResponse)
async def approve_join_request(
    request_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the join request
    join_request = db.query(ClubJoinRequest).filter(ClubJoinRequest.request_id == request_id).first()
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == join_request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or an admin
    is_club_leader = club.leader_id == current_user.user_id
    is_admin = current_user.role == 'admin'
    
    if not (is_club_leader or is_admin):
        raise HTTPException(
            status_code=403, 
            detail="Only club leader or admin can approve requests"
        )
    
    # Check if request is pending
    if join_request.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Request is already {join_request.status}")
    
    # Update request status
    join_request.status = 'approved'
    join_request.updated_at = datetime.now()
    
    # Create club membership
    new_membership = ClubMember(
        club_id=join_request.club_id,
        user_id=join_request.user_id
    )
    
    # Create notification for the user
    notification = Notification(
        user_id=join_request.user_id,
        notification_type="approval",
        reference_id=join_request.request_id,
        notification_text=f"Your request to join {club.club_name} has been approved",
        is_read=False,
        notification_date=datetime.now()
    )
    
    db.add(new_membership)
    db.add(notification)
    db.commit()
    db.refresh(join_request)
    
    return join_request

# Reject a join request (club leader only)
@app.put("/clubs/join-requests/{request_id}/reject", response_model=ClubJoinRequestResponse)
async def reject_join_request(
    request_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the join request
    join_request = db.query(ClubJoinRequest).filter(ClubJoinRequest.request_id == request_id).first()
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == join_request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is the club leader or an admin
    is_club_leader = club.leader_id == current_user.user_id
    is_admin = current_user.role == 'admin'
    
    if not (is_club_leader or is_admin):
        raise HTTPException(
            status_code=403, 
            detail="Only club leader or admin can reject requests"
        )
    
    # Check if request is pending
    if join_request.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Request is already {join_request.status}")
    
    # Update request status
    join_request.status = 'rejected'
    join_request.updated_at = datetime.now()
    
    # Create notification for the user
    notification = Notification(
        user_id=join_request.user_id,
        notification_type="rejection",
        reference_id=join_request.request_id,
        notification_text=f"Your request to join {club.club_name} has been rejected",
        is_read=False,
        notification_date=datetime.now()
    )
    
    db.add(notification)
    db.commit()
    db.refresh(join_request)
    
    return join_request