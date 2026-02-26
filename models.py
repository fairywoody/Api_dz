from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class SortField(str, Enum):
    date = "date"
    time = "time"
    rate = "rate"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class RateFilter(BaseModel):
    start_date: Optional[date] = Field(None, description="Начальная дата (включительно)")
    end_date: Optional[date] = Field(None, description="Конечная дата (включительно)")
    min_rate: Optional[float] = Field(None, ge=0, description="Минимальный курс")
    max_rate: Optional[float] = Field(None, ge=0, description="Максимальный курс")
    currency: Optional[str] = Field("USD/RUB", description="Валюта (по умолчанию USD/RUB)")

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date должен быть после start_date')
        return v


class RateResponse(BaseModel):
    id: int = Field(0, description="ID записи")  # Значение по умолчанию 0
    date: date
    time: str
    rate: float
    currency: str = "USD/RUB"
    timestamp: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        validate_assignment = False


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: List[RateResponse]
    has_next: bool
    has_prev: bool


class StatsResponse(BaseModel):
    currency: str
    period_start: date
    period_end: date
    average_rate: float
    min_rate: float
    min_rate_date: Optional[date]
    max_rate: float
    max_rate_date: Optional[date]
    records_count: int
    last_update: datetime


class APIError(BaseModel):
    detail: str
    error_code: Optional[str] = None