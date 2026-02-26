import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Tuple
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVStorage:

    def __init__(self, csv_file: str = "usd_rate.csv"):
        self.csv_file = csv_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        try:
            if not os.path.exists(self.csv_file):
                with open(self.csv_file, 'w', encoding='utf-8') as f:
                    f.write('Дата,Время,Курс USD/RUB,Timestamp\n')
                logger.info(f"Создан CSV файл: {self.csv_file}")
        except IOError as e:
            logger.error(f"Ошибка при создании CSV файла: {e}")
            raise

    def read_all(self) -> List[dict]:
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Ошибка при чтении CSV: {e}")
            return []

    def append(self, date_str: str, time_str: str, rate: float) -> bool:
        try:
            timestamp = f"{date_str} {time_str}"
            with open(self.csv_file, 'a', encoding='utf-8') as f:
                f.write(f"{date_str},{time_str},{rate},{timestamp}\n")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении в CSV: {e}")
            return False


class DatabaseStorage:

    def __init__(self, db_file: str = "currency.db"):
        self.db_file = db_file
        self.conn = None
        self._connect()
        self._create_table_if_not_exists()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Соединение с БД установлено: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")

    def _create_table_if_not_exists(self):
        try:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS currency_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    rate REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD/RUB'
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка при создании таблицы: {e}")
            raise

    def clear_table(self):
        try:
            self.conn.execute('DELETE FROM currency_rates')
            self.conn.commit()
            logger.info("Таблица очищена")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при очистке таблицы: {e}")
            raise

    def insert_many(self, records: List[dict]) -> int:
        if not records:
            return 0
        try:
            cursor = self.conn.cursor()
            data = [(r['timestamp'], r['rate'], r['currency']) for r in records]
            cursor.executemany(
                'INSERT INTO currency_rates (timestamp, rate, currency) VALUES (?, ?, ?)',
                data
            )
            self.conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Ошибка при массовой вставке: {e}")
            self.conn.rollback()
            return 0

    def insert_one(self, timestamp: str, rate: float, currency: str = "USD/RUB") -> Optional[int]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO currency_rates (timestamp, rate, currency) VALUES (?, ?, ?)',
                (timestamp, rate, currency)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Ошибка при вставке: {e}")
            self.conn.rollback()
            return None

    def execute_query(self, query: str, params: list = None) -> List[dict]:
        if params is None:
            params = []
        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return []

    def execute_query_with_count(self, query: str, params: list = None) -> Tuple[List[dict], int]:
        if params is None:
            params = []
        try:
            count_query = f"SELECT COUNT(*) as count FROM ({query})"
            count_result = self.conn.execute(count_query, params).fetchone()
            total_count = count_result['count'] if count_result else 0

            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()], total_count
        except sqlite3.Error as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return [], 0

    def get_record_count(self, currency: str = "USD/RUB") -> int:
        try:
            result = self.conn.execute(
                'SELECT COUNT(*) as cnt FROM currency_rates WHERE currency = ?',
                [currency]
            ).fetchone()
            return result['cnt'] if result else 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении количества записей: {e}")
            return 0


class CurrencyService:

    def __init__(self, csv_file: str = "usd_rate.csv", db_file: str = "currency.db"):
        self.csv = CSVStorage(csv_file)
        self.db = DatabaseStorage(db_file)
        self._initialized = False

    def _validate_date(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _validate_time(self, time_str: str) -> bool:
        try:
            datetime.strptime(time_str, "%H:%M:%S")
            return True
        except ValueError:
            return False

    def _validate_rate(self, rate: float) -> bool:
        return rate > 0

    def initialize_from_csv(self, force: bool = False) -> bool:
        try:
            if not force and self.db.get_record_count() > 0:
                logger.info("БД уже содержит данные, пропускаем инициализацию")
                self._initialized = True
                return True

            df = pd.read_csv(self.csv.csv_file, encoding='utf-8')

            records = []
            for _, row in df.iterrows():
                try:
                    if 'Timestamp' in row:
                        timestamp = row['Timestamp']
                        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%H:%M:%S")
                        rate_str = str(row['Курс USD/RUB']).replace(',', '.')
                    else:
                        date_str = row['Дата']
                        time_str = row['Время']
                        rate_str = str(row['Курс USD/RUB']).replace(',', '.')
                        timestamp = f"{date_str} {time_str}"

                    if not self._validate_date(date_str) or not self._validate_time(time_str):
                        logger.warning(f"Некорректная дата/время: {date_str} {time_str}")
                        continue

                    rate = float(rate_str)
                    if not self._validate_rate(rate):
                        logger.warning(f"Некорректный курс: {rate}")
                        continue

                    records.append({
                        'timestamp': timestamp,
                        'rate': rate,
                        'currency': 'USD/RUB'
                    })
                except Exception as e:
                    logger.warning(f"Ошибка при обработке строки: {e}")
                    continue

            if not records:
                logger.warning("Нет валидных записей в CSV")
                return False

            if force:
                self.db.clear_table()

            inserted = self.db.insert_many(records)
            logger.info(f"Импортировано {inserted} записей из CSV")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Ошибка при инициализации из CSV: {e}")
            return False

    def add_rate(self, date_str: str, time_str: str, rate: float, currency: str = "USD/RUB") -> bool:
        if not self._validate_date(date_str):
            raise ValueError(f"Некорректная дата: {date_str}")
        if not self._validate_time(time_str):
            raise ValueError(f"Некорректное время: {time_str}")
        if not self._validate_rate(rate):
            raise ValueError(f"Курс должен быть положительным: {rate}")

        timestamp = f"{date_str} {time_str}"

        record_id = self.db.insert_one(timestamp, rate, currency)
        if not record_id:
            return False

        self.csv.append(date_str, time_str, rate)

        return True

    def get_latest_rate(self, currency: str = "USD/RUB") -> Optional[dict]:
        try:
            query = '''
                SELECT * FROM currency_rates 
                WHERE currency = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            '''
            results = self.db.execute_query(query, [currency])

            if results and len(results) > 0:
                row = results[0]
                if 'timestamp' not in row or 'rate' not in row:
                    logger.error(f"Отсутствуют обязательные поля в результате: {row}")
                    return None

                record_id = row.get('id')
                if record_id is None:
                    record_id = 0
                    logger.warning(f"ID записи отсутствует, используем значение по умолчанию: {record_id}")

                dt = datetime.fromisoformat(row['timestamp'])
                return {
                    'id': record_id,
                    'date': dt.date(),
                    'time': dt.time().strftime('%H:%M:%S'),
                    'rate': float(row['rate']),
                    'currency': row.get('currency', currency),
                    'timestamp': row['timestamp']
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка в get_latest_rate: {e}")
            return None

    def get_rates(
            self,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            min_rate: Optional[float] = None,
            max_rate: Optional[float] = None,
            currency: str = "USD/RUB",
            sort_by: str = "date",
            sort_order: str = "desc",
            page: int = 1,
            page_size: int = 50
    ) -> Tuple[List[dict], int]:

        query = "SELECT * FROM currency_rates WHERE currency = ?"
        params = [currency]

        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date.isoformat())

        if min_rate is not None:
            query += " AND rate >= ?"
            params.append(min_rate)

        if max_rate is not None:
            query += " AND rate <= ?"
            params.append(max_rate)

        sort_field_map = {
            "date": "timestamp",
            "time": "timestamp",
            "rate": "rate"
        }
        sort_field = sort_field_map.get(sort_by, "timestamp")
        order_dir = "ASC" if sort_order.lower() == "asc" else "DESC"
        query += f" ORDER BY {sort_field} {order_dir}"

        offset = (page - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])

        results, total_count = self.db.execute_query_with_count(query, params)

        formatted = []
        for row in results:
            dt = datetime.fromisoformat(row['timestamp'])
            formatted.append({
                'id': row['id'],
                'date': dt.date(),
                'time': dt.time().strftime('%H:%M:%S'),
                'rate': row['rate'],
                'currency': row['currency'],
                'timestamp': row['timestamp']
            })

        return formatted, total_count

    def get_statistics(
            self,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            currency: str = "USD/RUB"
    ) -> Optional[dict]:

        query = '''
            SELECT 
                MIN(DATE(timestamp)) as period_start,
                MAX(DATE(timestamp)) as period_end,
                AVG(rate) as avg_rate,
                MIN(rate) as min_rate,
                MAX(rate) as max_rate,
                COUNT(*) as records_count,
                MAX(timestamp) as last_update
            FROM currency_rates 
            WHERE currency = ?
        '''
        params = [currency]

        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date.isoformat())

        results = self.db.execute_query(query, params)

        if not results or not results[0]['period_start']:
            return None

        stats = results[0]

        min_date_query = '''
            SELECT DATE(timestamp) as min_date 
            FROM currency_rates 
            WHERE currency = ? AND rate = ? 
            LIMIT 1
        '''
        min_date_result = self.db.execute_query(min_date_query, [currency, stats['min_rate']])

        max_date_query = '''
            SELECT DATE(timestamp) as max_date 
            FROM currency_rates 
            WHERE currency = ? AND rate = ? 
            LIMIT 1
        '''
        max_date_result = self.db.execute_query(max_date_query, [currency, stats['max_rate']])

        return {
            'currency': currency,
            'period_start': stats['period_start'],
            'period_end': stats['period_end'],
            'average_rate': round(stats['avg_rate'], 4) if stats['avg_rate'] else 0,
            'min_rate': stats['min_rate'],
            'min_rate_date': min_date_result[0]['min_date'] if min_date_result else None,
            'max_rate': stats['max_rate'],
            'max_rate_date': max_date_result[0]['max_date'] if max_date_result else None,
            'records_count': stats['records_count'],
            'last_update': stats['last_update']
        }


class CurrencyDatabase(CurrencyService):
    pass