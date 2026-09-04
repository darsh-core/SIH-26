import uuid
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import ErrorResponseEnvelope, ErrorDetail

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sih-platform")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Competency intelligence and learning platform for the official statistical system of India.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Error Handlers
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    # Determine error code from status or detail
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 409:
        code = "CONFLICT"
    elif exc.status_code == 400:
        code = "BAD_REQUEST"
        
    error_detail = ErrorDetail(
        code=code,
        message=str(exc.detail),
        request_id=str(uuid.uuid4())
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseEnvelope(error=error_detail).model_dump()
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Formulate validation errors list
    errors_str = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()])
    error_detail = ErrorDetail(
        code="VALIDATION_ERROR",
        message=f"Validation failed: {errors_str}",
        request_id=str(uuid.uuid4())
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponseEnvelope(error=error_detail).model_dump()
    )


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    error_detail = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please contact the administrator.",
        request_id=str(uuid.uuid4())
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponseEnvelope(error=error_detail).model_dump()
    )


# Health checks
@app.get("/health", summary="Basic Health Check")
def health_check():
    return {
        "status": "healthy",
        "service": "sih-competency-platform"
    }


@app.get("/health/db", summary="Database Connection Health Check")
def health_db_check(db: Session = Depends(get_db)):
    try:
        # Run a quick ping query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failure"
        )


@app.get("/health/ready", summary="Readiness Probe")
def health_ready_check():
    return {
        "status": "ready",
        "service": "sih-competency-platform"
    }


# Register Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.roles import router as roles_router
from app.api.v1.competencies import router as competencies_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.courses import router as courses_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.learning_plans import router as learning_plans_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ai import router as ai_router
from app.api.v1.copilot import router as copilot_router

from app.api.v1.learning import router as learning_router

# Mount v1 routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(profiles_router, prefix=settings.API_V1_STR)
app.include_router(roles_router, prefix=settings.API_V1_STR)
app.include_router(competencies_router, prefix=settings.API_V1_STR)
app.include_router(assessments_router, prefix=settings.API_V1_STR)
app.include_router(courses_router, prefix=settings.API_V1_STR)
app.include_router(learning_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(learning_plans_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(copilot_router, prefix=settings.API_V1_STR)
# Mount analytics endpoints (some have no prefix, registered directly inside router)
app.include_router(analytics_router, prefix=settings.API_V1_STR)

