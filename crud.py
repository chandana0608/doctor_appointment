from sqlmodel import Session, select
from .models import User, DoctorProfile
from .auth import get_password_hash

def create_user(session: Session, email: str, password: str, full_name: str, role: str, specialization: str | None = None):
    # bcrypt only processes the first 72 bytes of the password.
    # If a longer password is passed, the bcrypt backend raises ValueError.
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password is too long (bcrypt supports max 72 bytes).")

    user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)

    if user.id is None:
        raise ValueError("User id not generated")

    if role == "doctor":
        dp = DoctorProfile(user_id=int(user.id), specialization=specialization or "General")
        session.add(dp)
        session.commit()
        session.refresh(dp)
        return user, dp
    return user, None

def list_doctors(session: Session, specialization: str | None = None):
    stmt = select(DoctorProfile)
    if specialization:
        stmt = stmt.where(DoctorProfile.specialization == specialization)
    return session.exec(stmt).all()