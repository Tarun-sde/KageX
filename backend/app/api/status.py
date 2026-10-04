from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")


class Status(BaseModel):
    phase: Literal["static_analysis"] = "static_analysis"
    analysis_available: Literal[True] = True


@router.get("/status", response_model=Status)
def status() -> Status:
    return Status()
