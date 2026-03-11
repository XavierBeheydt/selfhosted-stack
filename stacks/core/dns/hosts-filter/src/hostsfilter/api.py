"""FastAPI application for Hosts Filter service."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from .hosts import generate_hosts_for_ip
from .config import Config


class FilterRequest(BaseModel):
    """Request model for filter configuration."""

    ip: str
    categories: List[str]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str


# Initialize FastAPI app
app = FastAPI(title="Hosts Filter Service", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/configure", response_model=dict)
async def configure_filter(
    request: FilterRequest, config: Config = Depends(Config)
):
    """Configure filtering for a specific IP address.

    Args:
        request: Filter configuration request

    Returns:
        Dictionary with status and file path

    Raises:
        HTTPException: If configuration fails
    """
    try:
        file_path = generate_hosts_for_ip(
            request.ip, request.categories, config.data_dir
        )
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")
