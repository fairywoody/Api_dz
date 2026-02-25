import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Tuple
import os


class CurrencyDatabase:
    def __init__(self, csv_file="usd_rate.csv", db_file="currency.db"):
        self.csv_file = csv_file
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', encoding='utf-8') as f:
                f.write('Дата,Время,Курс USD/RUB\n')

        conn = sqlite3.connect(self.db_file)

        df = pd.read_csv(self.csv_file, encoding='utf-8')

        df['timestamp'] = pd.to_datetime(df['Дата'] + ' ' + df['Время'])
        df['rate'] = df['Курс USD/RUB'].astype(float)
        df['currency'] = 'USD/RUB'

        df[['timestamp', 'rate', 'currency']].to_sql(
            'currency_rates',
            conn,
            if_exists='replace',
            index_label='id'
        )

        conn.close()

    def refresh_data(self):
        self.init_database()

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

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM currency_rates WHERE 1=1"
        params = []

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

        if currency:
            query += " AND currency = ?"
            params.append(currency)

        count_query = f"SELECT COUNT(*) as count FROM ({query})"
        total_count = conn.execute(count_query, params).fetchone()['count']

        order_by = ""
        if sort_by == "date":
            order_by = "DATE(timestamp)"
        elif sort_by == "time":
            order_by = "TIME(timestamp)"
        elif sort_by == "rate":
            order_by = "rate"
        else:
            order_by = "timestamp"

        order_dir = "ASC" if sort_order == "asc" else "DESC"
        query += f" ORDER BY {order_by} {order_dir}"

        offset = (page - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            result['date'] = datetime.fromisoformat(result['timestamp']).date()
            result['time'] = datetime.fromisoformat(result['timestamp']).time().strftime('%H:%M:%S')
            results.append(result)

        conn.close()

        return results, total_count

    def get_statistics(
            self,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            currency: str = "USD/RUB"
    ) -> Optional[dict]:

        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row

        query = """
        SELECT 
            currency,
            MIN(DATE(timestamp)) as period_start,
            MAX(DATE(timestamp)) as period_end,
            AVG(rate) as average_rate,
            MIN(rate) as min_rate,
            MAX(rate) as max_rate,
            COUNT(*) as records_count,
            MAX(timestamp) as last_update
        FROM currency_rates 
        WHERE currency = ?
        """
        params = [currency]

        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date.isoformat())

        result = conn.execute(query, params).fetchone()

        if not result:
            conn.close()
            return None

        min_rate_query = """
        SELECT DATE(timestamp) as date FROM currency_rates 
        WHERE rate = (SELECT MIN(rate) FROM currency_rates WHERE currency = ?)
        AND currency = ?
        LIMIT 1
        """
        min_date = conn.execute(min_rate_query, [currency, currency]).fetchone()

        max_rate_query = """
        SELECT DATE(timestamp) as date FROM currency_rates 
        WHERE rate = (SELECT MAX(rate) FROM currency_rates WHERE currency = ?)
        AND currency = ?
        LIMIT 1
        """
        max_date = conn.execute(max_rate_query, [currency, currency]).fetchone()

        conn.close()

        stats = dict(result)
        stats['min_rate_date'] = date.fromisoformat(min_date['date']) if min_date else None
        stats['max_rate_date'] = date.fromisoformat(max_date['date']) if max_date else None

        return stats

    def get_latest_rate(self, currency: str = "USD/RUB") -> Optional[dict]:

        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row

        query = """
        SELECT * FROM currency_rates 
        WHERE currency = ?
        ORDER BY timestamp DESC 
        LIMIT 1
        """

        row = conn.execute(query, [currency]).fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['date'] = datetime.fromisoformat(result['timestamp']).date()
            result['time'] = datetime.fromisoformat(result['timestamp']).time().strftime('%H:%M:%S')
            return result

        return None

    def add_rate(self, date_str: str, time_str: str, rate: float, currency: str = "USD/RUB") -> bool:
        try:
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO currency_rates (timestamp, rate, currency) VALUES (?, ?, ?)",
                (timestamp.isoformat(), rate, currency)
            )

            conn.commit()
            conn.close()

            with open(self.csv_file, 'a', encoding='utf-8') as f:
                f.write(f"{date_str},{time_str},{rate}\n")

            return True
        except Exception as e:
            print(f"Ошибка при добавлении курса: {e}")
            return False