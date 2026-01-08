from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import init_db
from .routers.auth_router import router as auth_router
from .routers.doctor_router import router as doctor_router
from .routers.appointment_router import router as appointment_router
from .template import router as frontend_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Virtual Doctor Appointment", lifespan=lifespan)

app.include_router(frontend_router)
app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(appointment_router)

@app.get("/api")
def root():
    return {"message": "Virtual Doctor Appointment API"}