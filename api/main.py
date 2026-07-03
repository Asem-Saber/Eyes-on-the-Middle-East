from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.v1.api import api_router

app = FastAPI(
    title="Chronos Intelligence API",
    description="Backend API for Al Jazeera Dashboard",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to the Chronos Intelligence API. Go to /docs for the API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
