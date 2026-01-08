from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..database import get_session
from ..auth import require_role, get_current_user
from ..models import Slot, Appointment, DoctorProfile, User
from ..schemas import AppointmentCreate, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentOut)
def book_appointment(
    payload: AppointmentCreate, 
    current_user: User = Depends(require_role("patient")), 
    session: Session = Depends(get_session)
):
    """Book an appointment with a doctor for a specific time slot"""
    
    patient_id = current_user.id
    if patient_id is None:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Check if doctor exists
    doctor = session.get(DoctorProfile, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Check if slot exists and belongs to the doctor
    slot = session.get(Slot, payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot.doctor_id != payload.doctor_id:
        raise HTTPException(status_code=400, detail="Slot does not belong to this doctor")
    
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot already booked")

    slot_id = slot.id
    if slot_id is None:
        raise HTTPException(status_code=500, detail="Slot id not generated")
    
    # Create the appointment
    appt = Appointment(
        doctor_id=payload.doctor_id, 
        patient_id=int(patient_id), 
        slot_id=int(slot_id), 
        reason=payload.reason
    )
    
    # Mark slot as booked
    slot.is_booked = True
    
    # Save to database
    session.add(appt)
    session.add(slot)
    session.commit()
    session.refresh(appt)
    
    return appt


@router.get("/me", response_model=List[AppointmentOut])
def my_appointments(
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
) -> list[Appointment]:
    """Get all appointments for the current user (patient or doctor)"""
    
    appointments: list[Appointment] = []

    if current_user.role == "patient":
        # Get appointments where user is the patient
        stmt = select(Appointment).where(Appointment.patient_id == current_user.id)
        appointments = list(session.exec(stmt).all())
        
    elif current_user.role == "doctor":
        # Find the doctor profile for this user
        stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
        doctor_profile = session.exec(stmt).first()
        
        if not doctor_profile:
            return appointments
        
        # Get appointments where user is the doctor
        stmt = select(Appointment).where(Appointment.doctor_id == doctor_profile.id)
        appointments = list(session.exec(stmt).all())
        
    else:
        appointments = []
    
    return appointments


@router.get("/", response_model=List[AppointmentOut])
def list_all_appointments(
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
) -> list[Appointment]:
    """List all appointments (admin only or filtered by user)"""
    
    appointments: list[Appointment] = []

    if current_user.role == "patient":
        stmt = select(Appointment).where(Appointment.patient_id == current_user.id)
    elif current_user.role == "doctor":
        stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
        doctor_profile = session.exec(stmt).first()
        if not doctor_profile:
            return appointments
        stmt = select(Appointment).where(Appointment.doctor_id == doctor_profile.id)
    else:
        stmt = select(Appointment)

    appointments = list(session.exec(stmt).all())
    return appointments


@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cancel an appointment"""
    
    appointment = session.get(Appointment, appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check if user has permission to cancel
    if current_user.role == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
    
    if current_user.role == "doctor":
        stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
        doctor_profile = session.exec(stmt).first()
        if not doctor_profile or appointment.doctor_id != doctor_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
    
    # Free up the slot
    if appointment.slot_id:
        slot = session.get(Slot, appointment.slot_id)
        if slot:
            slot.is_booked = False
            session.add(slot)
    
    # Delete appointment
    session.delete(appointment)
    session.commit()
    
    return {"message": "Appointment cancelled successfully"}