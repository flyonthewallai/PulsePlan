"""
Admin modules - consolidated admin endpoints
"""
from fastapi import APIRouter
from . import nlu

router = APIRouter()

# Include NLU monitoring endpoints
router.include_router(nlu.router, prefix="/nlu", tags=["admin-nlu"])

__all__ = ['router']
