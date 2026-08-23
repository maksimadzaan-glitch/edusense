"""Статистика проверенного банка заданий."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.bank import bank_stats

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.get("/stats")
def get_bank_stats(db: Session = Depends(get_db)):
    return bank_stats(db)
