# First, update the Notification model to match our requirements
class Notification(Base):
    __tablename__ = 'notifications'
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    notification_type = Column(String(50), default='general')  # join_request, approval, rejection, event_reminder, general
    reference_id = Column(Integer, nullable=True)  # Can store request_id, event_id, etc.
    notification_text = Column(Text)
    is_read = Column(Boolean, default=False)
    notification_date = Column(TIMESTAMP, default=datetime.now)
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    user = relationship("User")

# Notification Schemas
class NotificationResponse(BaseModel):
    notification_id: int
    notification_type: str
    reference_id: Optional[int] = None
    notification_text: str
    is_read: bool
    notification_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Get user notifications
@app.get("/users/me/notifications", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create base query
    query = db.query(Notification).filter(Notification.user_id == current_user.user_id)
    
    # Apply unread filter if requested
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    # Order by most recent first and limit results
    notifications = query.order_by(Notification.notification_date.desc()).limit(limit).all()
    
    return notifications

# Mark notification as read
@app.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the notification
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Mark as read
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    
    return notification

# Mark all notifications as read
@app.put("/users/me/notifications/read-all", response_model=dict)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Update all unread notifications for the current user
    result = db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": f"Marked {result} notifications as read"}

# Delete a notification
@app.delete("/notifications/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the notification
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Delete the notification
    db.delete(notification)
    db.commit()
    
    return None