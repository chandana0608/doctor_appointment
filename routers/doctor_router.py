from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..database import get_session
from ..auth import require_role
from ..schemas import DoctorOut, SlotCreate, SlotOut
from ..models import DoctorProfile, Slot, User

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=List[DoctorOut])
def get_doctors(specialization: str | None = None, session: Session = Depends(get_session)):
    stmt = select(DoctorProfile)
    if specialization:
        stmt = stmt.where(DoctorProfile.specialization == specialization)
    docs = session.exec(stmt).all()
    return docs

@router.post("/{doctor_id}/slots", response_model=SlotOut)
def create_slot(
    doctor_id: int,
    payload: SlotCreate,
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    stmt = select(DoctorProfile).where(DoctorProfile.id == doctor_id, DoctorProfile.user_id == current_user.id)
    doc = session.exec(stmt).first()
    if not doc:
        raise HTTPException(status_code=403, detail="You can only add slots for your own profile")
    
    # Validate that end_time is after start_time
    if payload.end_time and payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Check for overlapping slots (optional, but prevents confusion)
    stmt = select(Slot).where(
        Slot.doctor_id == doctor_id,
        Slot.is_booked == False
    )
    existing_slots = session.exec(stmt).all()
    for existing in existing_slots:
        if existing.end_time:
            # Check if new slot overlaps with existing slot
            if (payload.start_time < existing.end_time and 
                payload.end_time and payload.end_time > existing.start_time):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Slot overlaps with existing slot at {existing.start_time.strftime('%I:%M %p')}"
                )
    
    slot = Slot(doctor_id=doctor_id, start_time=payload.start_time, end_time=payload.end_time)
    session.add(slot)
    session.commit()
    session.refresh(slot)
    return slot

@router.get("/{doctor_id}/slots", response_model=List[SlotOut])
def list_slots(doctor_id: int, only_available: bool = True, session: Session = Depends(get_session)):
    stmt = select(Slot).where(Slot.doctor_id == doctor_id)
    if only_available:
        stmt = stmt.where(Slot.is_booked == False)
    slots = session.exec(stmt).all()
    return slots