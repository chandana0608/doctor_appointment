from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: str

    doctor_profile: Optional["DoctorProfile"] = Relationship(back_populates="user")
    appointments_as_patient: List["Appointment"] = Relationship(back_populates="patient")


class DoctorProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    specialization: str
    bio: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="doctor_profile")
    slots: List["Slot"] = Relationship(back_populates="doctor")
    appointments: List["Appointment"] = Relationship(back_populates="doctor")


class Slot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctorprofile.id")
    start_time: datetime
    end_time: Optional[datetime] = None
    is_booked: bool = Field(default=False)

    doctor: Optional[DoctorProfile] = Relationship(back_populates="slots")
    appointments: List["Appointment"] = Relationship(back_populates="slot")


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctorprofile.id")
    patient_id: int = Field(foreign_key="user.id")
    slot_id: Optional[int] = Field(foreign_key="slot.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None

    doctor: Optional[DoctorProfile] = Relationship(back_populates="appointments")
    patient: Optional[User] = Relationship(back_populates="appointments_as_patient")
    slot: Optional[Slot] = Relationship(back_populates="appointments")