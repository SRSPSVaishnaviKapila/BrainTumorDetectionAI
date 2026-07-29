from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.config import create_required_dirs
from app.routes import auth_routes, prediction_routes, report_routes, admin_routes, doctor_routes

app = FastAPI(
    title="Brain Tumor Detection API",
    description="FastAPI backend for MRI brain tumor detection using a trained deep learning model.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_required_dirs()
    init_db()


@app.get("/")
def root():
    return {
        "message": "Brain Tumor Detection API is running",
        "docs": "http://127.0.0.1:8000/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(auth_routes.router)
app.include_router(prediction_routes.router)
app.include_router(report_routes.router)
app.include_router(admin_routes.router)
app.include_router(doctor_routes.router)
