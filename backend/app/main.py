from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .errors import DomainError, InvalidTransitionError, NotFoundError, SlotUnavailableError
from .routers import bookings, catalog

app = FastAPI(title="GoDoc Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATUS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    SlotUnavailableError: 409,
    InvalidTransitionError: 409,
}


@app.exception_handler(DomainError)
def handle_domain_error(request: Request, exc: DomainError):
    code = next((c for cls, c in _STATUS.items() if isinstance(exc, cls)), 400)
    return JSONResponse(status_code=code, content={"detail": str(exc)})


app.include_router(catalog.router)
app.include_router(bookings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
