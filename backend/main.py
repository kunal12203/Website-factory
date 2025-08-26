# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import generate
import traceback # Import the traceback library

app = FastAPI(title="Website Factory API")

# --- THIS IS THE NEW CODE ---
# Add a global exception handler to catch all errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # This will print the full, detailed error traceback to your terminal
    print("--- A CRITICAL ERROR OCCURRED ---")
    traceback.print_exc() 
    
    # This returns a clean JSON response to the frontend
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred in the backend: {exc}"},
    )

# --- Configure CORS (Unchanged) ---
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include your API router (Unchanged) ---
app.include_router(generate.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "Website Factory API is running"}