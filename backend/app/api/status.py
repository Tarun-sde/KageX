from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")


class Status(BaseModel):
    phase: Literal["foundation"] = "foundation"
    analysis_available: Literal[False] = False


@router.get("/status", response_model=Status)
def status() -> Status:
    return Status()
