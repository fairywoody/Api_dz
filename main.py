from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
from datetime import date, datetime
import uvicorn
import logging
import traceback

from models import (
    RateResponse,
    PaginatedResponse,
    StatsResponse,
    SortField,
    SortOrder
)
from database import CurrencyDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Currency Rates API",
    description="API для получения курсов валют из базы данных скрапера",
    version="1.0.0",
)

db = CurrencyDatabase()

try:
    if db.initialize_from_csv(force=False):
        logger.info("База данных успешно инициализирована из CSV")
    else:
        logger.warning("Не удалось инициализировать из CSV, будет создана пустая БД")
except Exception as e:
    logger.error(f"Ошибка при инициализации из CSV: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(db, 'db') and db.db:
        db.db.close()
        logger.info("Соединение с БД закрыто")


@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        record_count = db.db.get_record_count() if hasattr(db, 'db') else 0
        latest = db.get_latest_rate()
        latest_info = f"{latest['date']} {latest['time']} - {latest['rate']}" if latest else "Нет данных"
    except:
        record_count = 0
        latest_info = "Нет данных"

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Currency Rates API</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 3em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }}

            .header p {{
                font-size: 1.2em;
                opacity: 0.95;
            }}

            .content {{
                padding: 40px;
            }}

            h2 {{
                color: #4a5568;
                margin: 30px 0 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #667eea;
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0 30px;
            }}

            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}

            .stat-card .number {{
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }}

            .stat-card .label {{
                font-size: 1.1em;
                opacity: 0.9;
            }}

            .endpoint {{
                background: #f7fafc;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                border-left: 5px solid #667eea;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}

            .method {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.9em;
                margin-right: 15px;
            }}

            .method.get {{ background: #48bb78; color: white; }}
            .method.post {{ background: #4299e1; color: white; }}

            .path {{
                font-family: 'Courier New', monospace;
                font-size: 1.3em;
                color: #2d3748;
                font-weight: bold;
            }}

            .description {{
                margin: 15px 0;
                color: #718096;
                font-size: 1.1em;
            }}

            .params {{
                background: #edf2f7;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
            }}

            .params-title {{
                font-weight: bold;
                color: #4a5568;
                margin-bottom: 10px;
            }}

            .param-item {{
                display: grid;
                grid-template-columns: 150px 1fr;
                padding: 8px 0;
                border-bottom: 1px solid #cbd5e0;
            }}

            .param-item:last-child {{
                border-bottom: none;
            }}

            .param-name {{
                font-family: 'Courier New', monospace;
                color: #e53e3e;
                font-weight: bold;
            }}

            .param-desc {{
                color: #4a5568;
            }}

            .test-button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin: 10px 0;
                transition: background 0.3s;
            }}

            .test-button:hover {{
                background: #5a67d8;
            }}

            .result-box {{
                background: #2d3748;
                color: #68d391;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                margin: 15px 0;
                overflow-x: auto;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }}

            .result-box.error {{
                color: #fc8181;
            }}

            .badge {{
                display: inline-block;
                background: #9f7aea;
                color: white;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.8em;
                margin-left: 10px;
            }}

            .footer {{
                text-align: center;
                padding: 20px;
                background: #f7fafc;
                color: #718096;
                border-top: 1px solid #e2e8f0;
            }}

            .loading {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-left: 10px;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}

            @media (max-width: 768px) {{
                .header h1 {{ font-size: 2em; }}
                .param-item {{ grid-template-columns: 1fr; }}
            }}

            .input-group {{
                display: flex;
                gap: 10px;
                margin: 10px 0;
                flex-wrap: wrap;
            }}

            .input-group input {{
                padding: 8px;
                border: 1px solid #cbd5e0;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                flex: 1;
                min-width: 200px;
            }}

            .input-group label {{
                display: flex;
                align-items: center;
                color: #4a5568;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 Currency Rates API</h1>
                <p>API для работы с курсами валют из базы данных скрапера</p>
                <div style="margin-top: 20px;">
                    <span class="badge">FastAPI</span>
                    <span class="badge">SQLite</span>
                    <span class="badge">REST API</span>
                </div>
            </div>

            <div class="content">
                <h2>📊 Статистика</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="label">Всего записей</div>
                        <div class="number">{record_count}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Последний курс</div>
                        <div class="number">{latest_info}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Статус сервера</div>
                        <div class="number">✅ Online</div>
                    </div>
                </div>

                <h2>🔧 Интерактивные эндпоинты</h2>
                <p>Нажмите на кнопку "Выполнить" чтобы отправить запрос и увидеть результат</p>

                <!-- Health Check -->
                <div class="endpoint">
                    <div>
                        <span class="method get">GET</span>
                        <span class="path">/health</span>
                    </div>
                    <div class="description">Проверка работоспособности сервера и подключения к БД</div>
                    <button class="test-button" onclick="testEndpoint('/health')">🚀 Выполнить</button>
                    <div id="result-health" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <!-- Latest Rate -->
                <div class="endpoint">
                    <div>
                        <span class="method get">GET</span>
                        <span class="path">/rates/latest</span>
                    </div>
                    <div class="description">Получить последний доступный курс валюты</div>
                    <div class="input-group">
                        <label>
                            Валюта:
                            <input type="text" id="currency-latest" value="USD/RUB" placeholder="USD/RUB">
                        </label>
                    </div>
                    <button class="test-button" onclick="testLatest()">🚀 Выполнить</button>
                    <div id="result-latest" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <!-- Rates List -->
                <div class="endpoint">
                    <div>
                        <span class="method get">GET</span>
                        <span class="path">/rates</span>
                    </div>
                    <div class="description">Получить список курсов с фильтрацией</div>
                    <div class="input-group">
                        <label>
                            Мин. курс:
                            <input type="number" id="min-rate" placeholder="90.0">
                        </label>
                        <label>
                            Макс. курс:
                            <input type="number" id="max-rate" placeholder="100.0">
                        </label>
                    </div>
                    <div class="input-group">
                        <label>
                            Начальная дата:
                            <input type="date" id="start-date">
                        </label>
                        <label>
                            Конечная дата:
                            <input type="date" id="end-date">
                        </label>
                    </div>
                    <div class="input-group">
                        <label>
                            Страница:
                            <input type="number" id="page" value="1" min="1">
                        </label>
                        <label>
                            Размер страницы:
                            <input type="number" id="page-size" value="5" min="1" max="100">
                        </label>
                    </div>
                    <div class="input-group">
                        <label>
                            Сортировка:
                            <select id="sort-by">
                                <option value="date">По дате</option>
                                <option value="rate">По курсу</option>
                            </select>
                        </label>
                        <label>
                            Порядок:
                            <select id="sort-order">
                                <option value="desc">Убывание</option>
                                <option value="asc">Возрастание</option>
                            </select>
                        </label>
                    </div>
                    <button class="test-button" onclick="testRates()">🚀 Выполнить</button>
                    <div id="result-rates" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <!-- Statistics -->
                <div class="endpoint">
                    <div>
                        <span class="method get">GET</span>
                        <span class="path">/rates/stats</span>
                    </div>
                    <div class="description">Получить статистику по курсам валюты</div>
                    <div class="input-group">
                        <label>
                            Начальная дата:
                            <input type="date" id="stats-start">
                        </label>
                        <label>
                            Конечная дата:
                            <input type="date" id="stats-end">
                        </label>
                    </div>
                    <button class="test-button" onclick="testStats()">🚀 Выполнить</button>
                    <div id="result-stats" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <!-- Add Rate -->
                <div class="endpoint">
                    <div>
                        <span class="method post">POST</span>
                        <span class="path">/rates</span>
                    </div>
                    <div class="description">Добавить новый курс</div>
                    <div class="input-group">
                        <label>
                            Дата:
                            <input type="date" id="add-date">
                        </label>
                        <label>
                            Время:
                            <input type="time" id="add-time" value="12:00">
                        </label>
                    </div>
                    <div class="input-group">
                        <label>
                            Курс:
                            <input type="number" id="add-rate" step="0.01" placeholder="90.5">
                        </label>
                        <label>
                            Валюта:
                            <input type="text" id="add-currency" value="USD/RUB">
                        </label>
                    </div>
                    <button class="test-button" onclick="testAddRate()">🚀 Выполнить</button>
                    <div id="result-add" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <!-- Refresh Database -->
                <div class="endpoint">
                    <div>
                        <span class="method post">POST</span>
                        <span class="path">/refresh</span>
                    </div>
                    <div class="description">Обновить базу данных из CSV файла</div>
                    <button class="test-button" onclick="testRefresh()">🚀 Выполнить</button>
                    <div id="result-refresh" class="result-box">Нажмите "Выполнить" для отправки запроса</div>
                </div>

                <h2>📝 Форматы ответов</h2>

                <div style="background: #f7fafc; border-radius: 10px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #4a5568; margin-bottom: 15px;">✅ Успешный ответ (200 OK)</h3>
                    <div class="result-box" style="color: #68d391;">
{{
    "page": 1,
    "page_size": 5,
    "total_items": 100,
    "total_pages": 20,
    "items": [
        {{
            "id": 1,
            "date": "2026-02-26",
            "time": "12:00:00",
            "rate": 90.5,
            "currency": "USD/RUB",
            "timestamp": "2026-02-26T12:00:00"
        }}
    ],
    "has_next": true,
    "has_prev": false
}}
                    </div>
                </div>

                <h2>⚠️ Ограничения</h2>

                <ul style="margin-left: 20px; color: #4a5568;">
                    <li>Максимальный размер страницы: 100 записей</li>
                    <li>Поддерживается только валюта USD/RUB (можно расширить)</li>
                    <li>Даты должны быть в формате YYYY-MM-DD</li>
                    <li>Время должно быть в формате HH:MM:SS</li>
                    <li>Курс должен быть положительным числом</li>
                </ul>
            </div>

            <div class="footer">
                <p>Currency Rates API v1.0.0 | FastAPI + SQLite</p>
                <p style="margin-top: 10px; font-size: 0.9em;">© 2026 Currency Rates API. Все права защищены.</p>
            </div>
        </div>

        <script>
            async function testEndpoint(url) {{
                const resultDiv = document.getElementById('result-health');
                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url);
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}

            async function testLatest() {{
                const currency = document.getElementById('currency-latest').value;
                const url = `/rates/latest?currency=${{encodeURIComponent(currency)}}`;
                const resultDiv = document.getElementById('result-latest');

                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url);
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}

            async function testRates() {{
                const params = new URLSearchParams();

                const minRate = document.getElementById('min-rate').value;
                const maxRate = document.getElementById('max-rate').value;
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                const page = document.getElementById('page').value;
                const pageSize = document.getElementById('page-size').value;
                const sortBy = document.getElementById('sort-by').value;
                const sortOrder = document.getElementById('sort-order').value;

                if (minRate) params.append('min_rate', minRate);
                if (maxRate) params.append('max_rate', maxRate);
                if (startDate) params.append('start_date', startDate);
                if (endDate) params.append('end_date', endDate);
                params.append('page', page);
                params.append('page_size', pageSize);
                params.append('sort_by', sortBy);
                params.append('sort_order', sortOrder);

                const url = `/rates?${{params.toString()}}`;
                const resultDiv = document.getElementById('result-rates');

                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url);
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}

            async function testStats() {{
                const params = new URLSearchParams();

                const startDate = document.getElementById('stats-start').value;
                const endDate = document.getElementById('stats-end').value;

                if (startDate) params.append('start_date', startDate);
                if (endDate) params.append('end_date', endDate);

                const url = `/rates/stats?${{params.toString()}}`;
                const resultDiv = document.getElementById('result-stats');

                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url);
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}

            async function testAddRate() {{
                const params = new URLSearchParams();

                const date = document.getElementById('add-date').value;
                const time = document.getElementById('add-time').value;
                const rate = document.getElementById('add-rate').value;
                const currency = document.getElementById('add-currency').value;

                if (!date || !time || !rate) {{
                    alert('Пожалуйста, заполните все поля');
                    return;
                }}

                params.append('date_str', date);
                params.append('time_str', time + ':00');
                params.append('rate', rate);
                params.append('currency', currency);

                const url = `/rates?${{params.toString()}}`;
                const resultDiv = document.getElementById('result-add');

                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url, {{
                        method: 'POST'
                    }});
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}

            async function testRefresh() {{
                const url = `/refresh`;
                const resultDiv = document.getElementById('result-refresh');

                resultDiv.innerHTML = '<span class="loading"></span> Загрузка...';
                resultDiv.classList.remove('error');

                try {{
                    const response = await fetch(url, {{
                        method: 'POST'
                    }});
                    const data = await response.json();
                    resultDiv.innerHTML = JSON.stringify(data, null, 2);
                    if (!response.ok) {{
                        resultDiv.classList.add('error');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Ошибка: ' + error.message;
                    resultDiv.classList.add('error');
                }}
            }}
        </script>
    </body>
    </html>
    """


@app.get("/rates/latest", response_model=RateResponse)
async def get_latest_rate(
        currency: str = Query("USD/RUB", description="Валюта")
):
    try:
        logger.info(f"GET /rates/latest с currency={currency}")

        rate = db.get_latest_rate(currency)

        if not rate:
            logger.warning(f"Курс для валюты {currency} не найден")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Курс для валюты {currency} не найден"}
            )

        logger.info(f"Найден курс: {rate}")
        return RateResponse(**rate)

    except Exception as e:
        logger.error(f"Ошибка в get_latest_rate: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Внутренняя ошибка сервера: {str(e)}"}
        )


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
    try:
        logger.info(f"GET /rates с параметрами: start_date={start_date}, end_date={end_date}, "
                   f"min_rate={min_rate}, max_rate={max_rate}, currency={currency}, "
                   f"sort_by={sort_by}, sort_order={sort_order}, page={page}, page_size={page_size}")

        if start_date and end_date and start_date > end_date:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Начальная дата не может быть больше конечной"}
            )

        if min_rate and max_rate and min_rate > max_rate:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Минимальный курс не может быть больше максимального"}
            )

        rates, total_count = db.get_rates(
            start_date=start_date,
            end_date=end_date,
            min_rate=min_rate,
            max_rate=max_rate,
            currency=currency,
            sort_by=sort_by.value if sort_by else "date",
            sort_order=sort_order.value if sort_order else "desc",
            page=page,
            page_size=page_size
        )

        logger.info(f"Получено {len(rates)} записей из БД, всего: {total_count}")

        rate_responses = []
        for rate in rates:
            try:
                rate_responses.append(RateResponse(**rate))
            except Exception as e:
                logger.error(f"Ошибка при преобразовании записи {rate}: {e}")

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

        response = PaginatedResponse(
            page=page,
            page_size=page_size,
            total_items=total_count,
            total_pages=total_pages,
            items=rate_responses,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        logger.info(f"Успешный ответ: {len(rate_responses)} записей")
        return response

    except Exception as e:
        logger.error(f"Ошибка в get_rates: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Внутренняя ошибка сервера: {str(e)}"}
        )


@app.get("/rates/stats", response_model=StatsResponse)
async def get_statistics(
        start_date: Optional[date] = Query(None, description="Начальная дата"),
        end_date: Optional[date] = Query(None, description="Конечная дата"),
        currency: str = Query("USD/RUB", description="Валюта")
):
    try:
        logger.info(f"GET /rates/stats с параметрами: start_date={start_date}, end_date={end_date}, currency={currency}")

        stats = db.get_statistics(
            start_date=start_date,
            end_date=end_date,
            currency=currency
        )

        if not stats:
            logger.warning(f"Статистика для валюты {currency} не найдена")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Статистика для валюты {currency} не найдена"}
            )

        response = StatsResponse(
            currency=stats['currency'],
            period_start=date.fromisoformat(stats['period_start']),
            period_end=date.fromisoformat(stats['period_end']),
            average_rate=stats['average_rate'],
            min_rate=stats['min_rate'],
            min_rate_date=date.fromisoformat(stats['min_rate_date']) if stats['min_rate_date'] else None,
            max_rate=stats['max_rate'],
            max_rate_date=date.fromisoformat(stats['max_rate_date']) if stats['max_rate_date'] else None,
            records_count=stats['records_count'],
            last_update=datetime.fromisoformat(stats['last_update'])
        )

        logger.info(f"Успешный ответ: {response}")
        return response

    except Exception as e:
        logger.error(f"Ошибка в get_statistics: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Внутренняя ошибка сервера: {str(e)}"}
        )


@app.post("/refresh")
async def refresh_database():
    try:
        logger.info("POST /refresh - обновление БД из CSV")
        success = db.initialize_from_csv(force=True)
        if success:
            logger.info("База данных успешно обновлена из CSV")
            return {"message": "База данных успешно обновлена", "status": "success"}
        else:
            logger.warning("Не удалось обновить базу данных")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Не удалось обновить базу данных", "status": "error"}
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении БД: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Ошибка: {str(e)}", "status": "error"}
        )


@app.post("/rates")
async def add_rate_endpoint(
        date_str: str = Query(..., description="Дата в формате YYYY-MM-DD"),
        time_str: str = Query(..., description="Время в формате HH:MM:SS"),
        rate: float = Query(..., ge=0, description="Курс"),
        currency: str = Query("USD/RUB", description="Валюта")
):
    try:
        logger.info(f"POST /rates с параметрами: date={date_str}, time={time_str}, rate={rate}, currency={currency}")

        success = db.add_rate(date_str, time_str, rate, currency)
        if success:
            logger.info(f"Курс успешно добавлен: {date_str} {time_str} {rate} {currency}")
            return {"message": "Курс успешно добавлен", "status": "success"}
        else:
            logger.warning("Не удалось добавить курс")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Не удалось добавить курс", "status": "error"}
            )
    except ValueError as e:
        logger.warning(f"Ошибка валидации: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e), "status": "error"}
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении курса: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Внутренняя ошибка сервера: {str(e)}", "status": "error"}
        )


@app.get("/health")
async def health_check():
    try:
        record_count = db.db.get_record_count() if hasattr(db, 'db') else 0
        latest = db.get_latest_rate()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "connected",
                "records": record_count,
                "last_record": latest['timestamp'] if latest else None
            },
            "service": {
                "name": "Currency Rates API",
                "version": "1.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "error",
                "error": str(e)
            },
            "service": {
                "name": "Currency Rates API",
                "version": "1.0.0"
            }
        }


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
            <head>
                <title>404 - Страница не найдена</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0;
                        padding: 20px;
                    }
                    .error-box {
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 500px;
                    }
                    h1 {
                        color: #e53e3e;
                        font-size: 3em;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #4a5568;
                        font-size: 1.2em;
                        margin-bottom: 30px;
                    }
                    a {
                        display: inline-block;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-decoration: none;
                        padding: 12px 30px;
                        border-radius: 8px;
                        font-weight: bold;
                        transition: transform 0.2s;
                    }
                    a:hover {
                        transform: translateY(-2px);
                    }
                </style>
            </head>
            <body>
                <div class="error-box">
                    <h1>404</h1>
                    <p>Запрашиваемая страница не существует</p>
                    <a href="/">Вернуться на главную</a>
                </div>
            </body>
        </html>
        """,
        status_code=404
    )


if __name__ == "__main__":
    try:
        if db.db.get_record_count() == 0:
            logger.info("БД пуста, инициализация из CSV...")
            db.initialize_from_csv(force=True)
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )