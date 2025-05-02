from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from api.database.connection import get_db
from api.models.models import Club, ClubMember, User, ClubJoinRequest
from api.schemas.schemas import (
    ClubResponse, ClubCreate, ClubMemberResponse, ClubMemberWithUserResponse, 
    UserResponse, JoinRequestCreate, JoinRequestResponse, JoinRequestWithUserResponse,
    JoinRequestAction
)
from api.auth.utils import get_current_user

router = APIRouter(
    tags=["clubs"]
)

@router.get("/clubs", response_model=List[ClubResponse])
async def get_clubs(db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    return db.query(Club).all()

@router.get("/clubs/{club_id}", response_model=ClubResponse)
async def get_club(club_id: int, db: Session = Depends(get_db), 
                 current_user: User = Depends(get_current_user)):
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.post("/clubs", response_model=ClubResponse)
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

@router.get("/clubs/{club_id}/members", response_model=List[ClubMemberWithUserResponse])
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
    
    # Prepare the response that includes the leader
    response = list(club_members)  # Convert to list from SQLAlchemy result
    
    # Check if leader is already in the members list
    leader_already_in_members = any(
        member.user_id == club.leader_id for member in response
    )
    
    # If leader is not in members list, add the leader
    if not leader_already_in_members and club.leader_id:
        # Get the leader user object
        leader = db.query(User).filter(User.user_id == club.leader_id).first()
        if leader:
            # Check if a membership record exists
            leader_membership = db.query(ClubMember).filter(
                ClubMember.club_id == club_id,
                ClubMember.user_id == club.leader_id
            ).first()
            
            if not leader_membership:
                # Create a temporary membership for response
                # This doesn't save to the database
                leader_membership = ClubMember(
                    club_id=club_id,
                    user_id=club.leader_id,
                    user=leader  # Attach the user object
                )
                # Add leader at the beginning of the list
                response.insert(0, leader_membership)
    
    return response

# JOIN REQUEST ENDPOINTS

@router.post("/clubs/{club_id}/request-join", response_model=JoinRequestResponse)
async def request_to_join_club(
    club_id: int, 
    request_data: JoinRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request to join a club. This creates a pending request that needs approval from the club leader."""
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
    
    # Check if already has a pending request
    existing_request = db.query(ClubJoinRequest).filter(
        ClubJoinRequest.club_id == club_id,
        ClubJoinRequest.user_id == current_user.user_id,
        ClubJoinRequest.status == 'pending'
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending join request for this club")
    
    # Create new join request
    new_request = ClubJoinRequest(
        club_id=club_id,
        user_id=current_user.user_id,
        request_message=request_data.request_message,
        status='pending'
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/clubs/{club_id}/join-requests", response_model=List[JoinRequestWithUserResponse])
async def get_club_join_requests(
    club_id: int, 
    status: str = 'pending',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all join requests for a club. Only the club leader or admins can access this."""
    # Check if club exists
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is authorized (club leader or admin)
    is_club_leader = current_user.user_id == club.leader_id
    is_admin = current_user.role == 'admin'
    
    if not (is_club_leader or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club leader or admins can view join requests"
        )
    
    # Get all join requests with specified status
    join_requests = db.query(ClubJoinRequest).filter(
        ClubJoinRequest.club_id == club_id,
        ClubJoinRequest.status == status
    ).options(
        joinedload(ClubJoinRequest.user)
    ).all()
    
    return join_requests

@router.post("/clubs/join-requests/{request_id}/action", response_model=JoinRequestResponse)
async def process_join_request(
    request_id: int, 
    action_data: JoinRequestAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a join request. Only the club leader or admins can perform this action."""
    # Get the join request
    join_request = db.query(ClubJoinRequest).filter(
        ClubJoinRequest.request_id == request_id
    ).first()
    
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    
    # Get the club
    club = db.query(Club).filter(Club.club_id == join_request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check if user is authorized (club leader or admin)
    is_club_leader = current_user.user_id == club.leader_id
    is_admin = current_user.role == 'admin'
    
    if not (is_club_leader or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club leader or admins can approve/reject join requests"
        )
    
    # Process the action
    if action_data.action == 'approve':
        # Update request status
        join_request.status = 'approved'
        
        # Create club membership
        new_membership = ClubMember(
            club_id=join_request.club_id,
            user_id=join_request.user_id
        )
        db.add(new_membership)
    
    elif action_data.action == 'reject':
        # Update request status
        join_request.status = 'rejected'
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
    
    db.commit()
    db.refresh(join_request)
    return join_request

@router.get("/users/me/join-requests", response_model=List[JoinRequestWithUserResponse])
async def get_my_join_requests(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all join requests for the current user."""
    query = db.query(ClubJoinRequest).filter(
        ClubJoinRequest.user_id == current_user.user_id
    )
    
    if status:
        query = query.filter(ClubJoinRequest.status == status)
    
    join_requests = query.options(
        joinedload(ClubJoinRequest.club)
    ).all()
    
    return join_requests

# Original direct join endpoint - consider deprecating in favor of the request-approve flow
@router.post("/clubs/{club_id}/join", response_model=ClubMemberResponse)
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

@router.delete("/clubs/{club_id}/leave", status_code=204)
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