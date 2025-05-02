from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from api.database.connection import get_db
from api.models.models import User, ClubMember
from api.schemas.schemas import UserResponse, ClubMemberWithClubResponse, RoleAssignRequest, ProfilePictureUpdate, ProfileUpdate
from api.auth.utils import get_current_user

router = APIRouter(
    tags=["users"]
)

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # No placeholder generation, just return the user as is
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Get all users regardless of role"""
    return db.query(User).all()

@router.get("/students", response_model=List[UserResponse])
async def get_students(db: Session = Depends(get_db), 
                      current_user: User = Depends(get_current_user)):
    """
    This endpoint now returns all users, not just students, for backward compatibility.
    For filtering by role, use the /users endpoint with a query parameter.
    """
    try:
        return db.query(User).all()
    except Exception as e:
        print(f"Error in get_students: {str(e)}")
        # Return an empty list instead of raising an error
        return []

# Note: This is a separate route specifically for /users/me/clubs
@router.get("/users/me/clubs", response_model=List[ClubMemberWithClubResponse])
async def get_my_clubs(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    # Get all clubs the current user is a member of with club data
    user_clubs = db.query(ClubMember).filter(
        ClubMember.user_id == current_user.user_id
    ).options(
        joinedload(ClubMember.club)
    ).all()
    
    return user_clubs

@router.get("/users/{user_id}/clubs", response_model=List[ClubMemberWithClubResponse])
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

@router.post("/admin/assign_role")
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

@router.put("/users/me/profile-picture", response_model=UserResponse)
async def update_profile_picture(
    profile_data: ProfilePictureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the current user's profile picture (base64 encoded image)"""
    # Update the profile picture in the database
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set the new profile picture
    user.profile_picture = profile_data.profile_picture
    
    # Commit changes to the database
    db.commit()
    db.refresh(user)
    
    # Return the updated user
    return user

@router.delete("/users/me/profile-picture", response_model=UserResponse)
async def clear_profile_picture(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear the current user's profile picture"""
    # Get the current user from the database
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clear the profile picture
    user.profile_picture = None
    
    # Commit changes to the database
    db.commit()
    db.refresh(user)
    
    # Return the updated user
    return user

@router.put("/users/me/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the current user's profile information (bio, about_me, phone_number, interests)"""
    # Get the current user from the database
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the fields if provided
    if profile_data.bio is not None:
        user.bio = profile_data.bio
    if profile_data.about_me is not None:
        user.about_me = profile_data.about_me
    if profile_data.phone_number is not None:
        user.phone_number = profile_data.phone_number
    if profile_data.interests is not None:
        user.interests = profile_data.interests
    
    # Commit changes to the database
    db.commit()
    db.refresh(user)
    
    # Return the updated user
    return user 

@router.put("/users/me/complete-profile", response_model=UserResponse)
async def update_complete_profile(
    profile_data: CompleteProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the complete profile of the current user.
    This endpoint is specifically designed to work with EditProfile.qml
    and allows updating any or all user profile fields.
    Only the fields provided in the request will be updated.
    """
    # Get the current user from the database
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update each field if provided in the request
    if profile_data.first_name is not None:
        user.first_name = profile_data.first_name
        
    if profile_data.last_name is not None:
        user.last_name = profile_data.last_name
        
    if profile_data.date_of_birth is not None:
        user.date_of_birth = profile_data.date_of_birth
        
    if profile_data.bio is not None:
        user.bio = profile_data.bio
        
    if profile_data.about_me is not None:
        user.about_me = profile_data.about_me
        
    if profile_data.phone_number is not None:
        user.phone_number = profile_data.phone_number
        
    if profile_data.interests is not None:
        user.interests = profile_data.interests
    
    if profile_data.profile_picture is not None:
        user.profile_picture = profile_data.profile_picture
    
    # Commit changes to the database
    db.commit()
    db.refresh(user)
    
    # Return the updated user
    return user 
