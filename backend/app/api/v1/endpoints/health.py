from fastapi import APIRouter, HTTPException, status
from app.observability.health import health_manager

router = APIRouter()

@router.get("/health")
async def basic_health_check():
    """Basic health check endpoint"""
    try:
        health_status = await health_manager.basic_health()
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status"""
    try:
        health_status = await health_manager.detailed_health()
        
        # Return appropriate status code based on health
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        is_ready = await health_manager.readiness_check()
        
        if is_ready:
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    try:
        is_alive = await health_manager.liveness_check()
        
        if is_alive:
            return {"status": "alive"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not alive"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Liveness check failed: {str(e)}"
        )