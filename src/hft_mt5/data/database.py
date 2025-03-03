"""Database handling for trade history and performance metrics."""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from ..utils.logger import logger

class Database:
    """SQLite database manager for storing trade and performance data."""
    
    def __init__(self, db_path: str = "hft_strategy.db"):
        self.db_path = db_path
        self.initialize_tables()
        
    def initialize_tables(self):
        """Create necessary database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    ticket INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    volume REAL NOT NULL,
                    open_price REAL NOT NULL,
                    open_time INTEGER NOT NULL,
                    close_price REAL,
                    close_time INTEGER,
                    stop_loss REAL,
                    take_profit REAL,
                    profit REAL,
                    commission REAL,
                    swap REAL
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    timestamp INTEGER PRIMARY KEY,
                    trades_per_second REAL,
                    signals_per_second REAL,
                    drawdown REAL,
                    equity REAL,
                    execution_latency REAL
                )
            """)
            
            conn.commit()
    
    def store_trade(self, trade: Dict):
        """Store a new trade in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    ticket, symbol, type, volume, open_price, open_time,
                    stop_loss, take_profit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade['ticket'],
                trade['symbol'],
                trade['type'],
                trade['volume'],
                trade['open_price'],
                int(trade['open_time'].timestamp()),
                trade.get('stop_loss', 0),
                trade.get('take_profit', 0)
            ))
            conn.commit()
    
    def update_trade(self, ticket: int, close_data: Dict):
        """Update trade with closing information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trades 
                SET close_price = ?, close_time = ?, profit = ?,
                    commission = ?, swap = ?
                WHERE ticket = ?
            """, (
                close_data['close_price'],
                int(close_data['close_time'].timestamp()),
                close_data['profit'],
                close_data.get('commission', 0),
                close_data.get('swap', 0),
                ticket
            ))
            conn.commit()
    
    def store_metrics(self, metrics: Dict):
        """Store performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    timestamp, trades_per_second, signals_per_second,
                    drawdown, equity, execution_latency
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(datetime.now().timestamp()),
                metrics['trades_per_second'],
                metrics['signals_per_second'],
                metrics['drawdown'],
                metrics['equity'],
                metrics['execution_latency']
            ))
            conn.commit()
    
    def get_trade_history(self, 
                         symbol: Optional[str] = None, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> pd.DataFrame:
        """Get trade history as a pandas DataFrame."""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_time:
            query += " AND open_time >= ?"
            params.append(int(start_time.timestamp()))
        
        if end_time:
            query += " AND open_time <= ?"
            params.append(int(end_time.timestamp()))
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            
            # Convert timestamps to datetime
            for col in ['open_time', 'close_time']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], unit='s')
                    
            return df
    
    def get_performance_metrics(self, 
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> pd.DataFrame:
        """Get performance metrics as a pandas DataFrame."""
        query = "SELECT * FROM performance_metrics WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(int(start_time.timestamp()))
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(int(end_time.timestamp()))
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            return df
