from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str
    specialization: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Login(BaseModel):
    email: EmailStr
    password: str

class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    specialization: str
    bio: Optional[str] = None

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None

class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_booked: bool

class AppointmentCreate(BaseModel):
    doctor_id: int
    slot_id: int
    reason: Optional[str] = None

class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    doctor_id: int
    patient_id: int
    slot_id: Optional[int]
    created_at: datetime
    reason: Optional[str]