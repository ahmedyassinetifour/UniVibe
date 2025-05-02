# Academic Performance model class
class AcademicPerformance(Base):
    __tablename__ = 'academic_performance'
    performance_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    course_name = Column(String(100))
    grade = Column(String(5))
    semester = Column(String(20))
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    user = relationship("User")

# Academic Performance Schemas
class AcademicPerformanceCreate(BaseModel):
    course_name: str
    grade: str
    semester: str

class AcademicPerformanceUpdate(BaseModel):
    course_name: Optional[str] = None
    grade: Optional[str] = None
    semester: Optional[str] = None

class AcademicPerformanceResponse(BaseModel):
    performance_id: int
    course_name: str
    grade: str
    semester: str
    created_at: datetime

    class Config:
        from_attributes = True

# Add academic performance record
@app.post("/users/me/academic-performance", response_model=AcademicPerformanceResponse)
async def add_academic_performance(
    performance_data: AcademicPerformanceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create new academic performance record
    new_performance = AcademicPerformance(
        user_id=current_user.user_id,
        course_name=performance_data.course_name,
        grade=performance_data.grade,
        semester=performance_data.semester
    )
    
    db.add(new_performance)
    db.commit()
    db.refresh(new_performance)
    
    return new_performance

# Get current user's academic performance records
@app.get("/users/me/academic-performance", response_model=List[AcademicPerformanceResponse])
async def get_my_academic_performance(
    semester: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create base query
    query = db.query(AcademicPerformance).filter(AcademicPerformance.user_id == current_user.user_id)
    
    # Apply semester filter if provided
    if semester:
        query = query.filter(AcademicPerformance.semester == semester)
    
    # Get records
    performances = query.order_by(AcademicPerformance.semester).all()
    
    return performances

# Update academic performance record
@app.put("/users/me/academic-performance/{performance_id}", response_model=AcademicPerformanceResponse)
async def update_academic_performance(
    performance_id: int,
    performance_data: AcademicPerformanceUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the performance record
    performance = db.query(AcademicPerformance).filter(
        AcademicPerformance.performance_id == performance_id,
        AcademicPerformance.user_id == current_user.user_id
    ).first()
    
    if not performance:
        raise HTTPException(status_code=404, detail="Academic performance record not found")
    
    # Update fields that are provided
    for key, value in performance_data.dict(exclude_unset=True).items():
        setattr(performance, key, value)
    
    db.commit()
    db.refresh(performance)
    
    return performance

# Delete academic performance record
@app.delete("/users/me/academic-performance/{performance_id}", status_code=204)
async def delete_academic_performance(
    performance_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the performance record
    performance = db.query(AcademicPerformance).filter(
        AcademicPerformance.performance_id == performance_id,
        AcademicPerformance.user_id == current_user.user_id
    ).first()
    
    if not performance:
        raise HTTPException(status_code=404, detail="Academic performance record not found")
    
    # Delete the record
    db.delete(performance)
    db.commit()
    
    return None