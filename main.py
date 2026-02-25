from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import date, datetime
import uvicorn

from models import (
    RateResponse,
    PaginatedResponse,
    StatsResponse,
    SortField,
    SortOrder
)
from database import CurrencyDatabase

app = FastAPI(
    title="Currency Rates API",
    description="API для получения курсов валют из базы данных скрапера",
    version="1.0.0",
)

db = CurrencyDatabase()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Currency Rates API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .endpoint { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 5px solid #3498db; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .method { display: inline-block; background: #27ae60; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 14px; }
                .path { font-family: 'Courier New', monospace; font-size: 20px; margin-left: 15px; color: #2980b9; font-weight: bold; }
                .description { margin: 15px 0 10px 0; color: #7f8c8d; }
                .param { background: #f1f1f1; padding: 8px; margin: 8px 0; border-radius: 4px; font-family: 'Courier New', monospace; }
                .param strong { color: #e67e22; }
                code { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; color: #c0392b; }
                .note { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }
                .example { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; }
            </style>
        </head>
        <body>
            <h1>💰 Currency Rates API</h1>
            <p>API для работы с курсами валют из базы данных скрапера</p>

            <h2>🔧 Доступные эндпоинты:</h2>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/health</span>
                <div class="description">Проверка работоспособности сервера и подключения к БД</div>
                <div class="param"><strong>Пример:</strong> <a href="/health">/health</a></div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/rates/latest</span>
                <div class="description">Получить последний доступный курс валюты</div>
                <div class="param"><strong>Параметры:</strong> currency (по умолчанию USD/RUB)</div>
                <div class="param"><strong>Пример:</strong> <a href="/rates/latest">/rates/latest</a></div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/rates</span>
                <div class="description">Получить список курсов с фильтрацией, сортировкой и пагинацией</div>
                <div class="param">
                    <strong>Параметры:</strong><br>
                    • start_date: начальная дата (YYYY-MM-DD)<br>
                    • end_date: конечная дата (YYYY-MM-DD)<br>
                    • min_rate: минимальный курс<br>
                    • max_rate: максимальный курс<br>
                    • currency: валюта (по умолчанию USD/RUB)<br>
                    • sort_by: поле сортировки (date/time/rate)<br>
                    • sort_order: порядок (asc/desc)<br>
                    • page: номер страницы (по умолчанию 1)<br>
                    • page_size: размер страницы (1-100, по умолчанию 50)
                </div>
                <div class="param"><strong>Пример:</strong> <a href="/rates?page=1&page_size=5">/rates?page=1&page_size=5</a></div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/rates/stats</span>
                <div class="description">Получить статистику по курсам валюты</div>
                <div class="param"><strong>Параметры:</strong> start_date, end_date, currency</div>
                <div class="param"><strong>Пример:</strong> <a href="/rates/stats">/rates/stats</a></div>
            </div>

            <div class="endpoint">
                <span class="method">POST</span>
                <span class="path">/refresh</span>
                <div class="description">Обновить базу данных из CSV файла (административный)</div>
                <div class="param"><strong>Пример:</strong> curl -X POST http://localhost:8000/refresh</div>
            </div>

            <h2>📊 Примеры запросов:</h2>

            <div class="example">
                # Последний курс<br>
                curl http://localhost:8000/rates/latest<br>
                <br>
                # Курсы за последнюю неделю<br>
                curl "http://localhost:8000/rates?start_date=2026-02-18&end_date=2026-02-25"<br>
                <br>
                # Курсы выше 90.5 (сортировка по убыванию)<br>
                curl "http://localhost:8000/rates?min_rate=90.5&sort_by=rate&sort_order=desc"<br>
                <br>
                # Статистика за февраль<br>
                curl "http://localhost:8000/rates/stats?start_date=2026-02-01&end_date=2026-02-28"
            </div>

            <h2>🐍 Пример на Python:</h2>

            <div class="example">
                import requests<br>
                <br>
                # Получить последний курс<br>
                response = requests.get("http://localhost:8000/rates/latest")<br>
                print(response.json())<br>
                <br>
                # Получить курсы с фильтрацией<br>
                response = requests.get(<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"http://localhost:8000/rates",<br>
                &nbsp;&nbsp;&nbsp;&nbsp;params={ "min_rate": 90.0, "page_size": 10 }<br>
                )<br>
                print(response.json())
            </div>

            <hr>
            <p style="color: #7f8c8d; text-align: center; margin-top: 30px;">
                FastAPI приложение | Currency Rates API v1.0.0
            </p>
        </body>
    </html>
    """


@app.get("/rates", response_model=PaginatedResponse)
async def get_rates(
        start_date: Optional[date] = Query(None, description="Начальная дата фильтрации (включительно)"),
        end_date: Optional[date] = Query(None, description="Конечная дата фильтрации (включительно)"),
        min_rate: Optional[float] = Query(None, ge=0, description="Минимальный курс"),
        max_rate: Optional[float] = Query(None, ge=0, description="Максимальный курс"),
        currency: str = Query("USD/RUB", description="Валюта"),
        sort_by: SortField = Query(SortField.date, description="Поле для сортировки"),
        sort_order: SortOrder = Query(SortOrder.desc, description="Порядок сортировки"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(50, ge=1, le=100, description="Размер страницы (1-100)")
):

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Начальная дата не может быть больше конечной"
        )

    if min_rate and max_rate and min_rate > max_rate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Минимальный курс не может быть больше максимального"
        )

    rates, total_count = db.get_rates(
        start_date=start_date,
        end_date=end_date,
        min_rate=min_rate,
        max_rate=max_rate,
        currency=currency,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        page_size=page_size
    )

    if not rates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курсы по заданным критериям не найдены"
        )

    rate_responses = [RateResponse(**rate) for rate in rates]

    total_pages = (total_count + page_size - 1) // page_size

    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total_items=total_count,
        total_pages=total_pages,
        items=rate_responses,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@app.get("/rates/latest", response_model=RateResponse)
async def get_latest_rate(
        currency: str = Query("USD/RUB", description="Валюта")
):

    rate = db.get_latest_rate(currency)

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Курс для валюты {currency} не найден"
        )

    return RateResponse(**rate)


@app.get("/rates/stats", response_model=StatsResponse)
async def get_statistics(
        start_date: Optional[date] = Query(None, description="Начальная дата"),
        end_date: Optional[date] = Query(None, description="Конечная дата"),
        currency: str = Query("USD/RUB", description="Валюта")
):

    stats = db.get_statistics(
        start_date=start_date,
        end_date=end_date,
        currency=currency
    )

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Статистика для валюты {currency} не найдена"
        )

    return StatsResponse(
        currency=stats['currency'],
        period_start=date.fromisoformat(stats['period_start']),
        period_end=date.fromisoformat(stats['period_end']),
        average_rate=round(stats['average_rate'], 4),
        min_rate=stats['min_rate'],
        min_rate_date=stats['min_rate_date'],
        max_rate=stats['max_rate'],
        max_rate_date=stats['max_rate_date'],
        records_count=stats['records_count'],
        last_update=datetime.fromisoformat(stats['last_update'])
    )


@app.post("/refresh")
async def refresh_database():

    try:
        db.refresh_data()
        return {"message": "База данных успешно обновлена"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении базы данных: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disconnected"
    }


# Обработчик 404
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return HTMLResponse(
        content="""
        <html>
            <head><title>404 - Страница не найдена</title></head>
            <body>
                <h1>404 - Страница не найдена</h1>
                <p>Запрашиваемая страница не существует.</p>
                <p><a href="/">Вернуться на главную</a></p>
            </body>
        </html>
        """,
        status_code=404
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )