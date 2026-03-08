import sqlite3
from datetime import datetime, timedelta
import os
from typing import List, Dict

class ExposureTimelineManager:
    def __init__(self, db_path: str = "exposure_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exposure_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    plsi_score REAL,
                    pm25 REAL,
                    ozone REAL,
                    breathing_rate REAL,
                    interpretation TEXT
                )
            ''')
            conn.commit()

    def log_exposure(self, plsi_score: float, pollutants: Dict, breathing_rate: float, interpretation: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exposure_logs (plsi_score, pm25, ozone, breathing_rate, interpretation)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                plsi_score, 
                pollutants.get('pm25', 0), 
                pollutants.get('o3', 0), 
                breathing_rate,
                interpretation
            ))
            conn.commit()

    def get_timeline(self, hours: int = 24) -> List[Dict]:
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exposure_logs WHERE timestamp > ? ORDER BY timestamp ASC', (since,))
            return [dict(row) for row in cursor.fetchall()]

    def calculate_cumulative_dose(self, hours: int = 24) -> Dict:
        history = self.get_timeline(hours)
        if not history:
            return {"total_pm25_dose": 0, "status": "No data"}
            
        total_pm25 = 0
        interval_minutes = 10 
        
        for entry in history:
            total_pm25 += entry['pm25'] * (entry['breathing_rate'] / 1000.0) * interval_minutes
            
        return {
            "period_hours": hours,
            "total_pm25_exposed_micrograms": round(total_pm25, 2),
            "data_points": len(history),
            "trend": "unknown" if len(history) < 2 else ("rising" if history[-1]['plsi_score'] > history[0]['plsi_score'] else "falling")
        }
