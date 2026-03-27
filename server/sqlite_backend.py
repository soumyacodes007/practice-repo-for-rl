"""
SQLite backend for LLM Text2SQL Failure Gym.

Creates and manages SQLite database with realistic e-commerce data.
Executes SQL commands safely and measures execution time.
"""

import sqlite3
import time
import logging
import random
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SQLiteBackend:
    """
    Manages SQLite database with e-commerce data.
    Executes SQL commands safely and measures performance.
    """
    
    def __init__(self, db_path: str = None, seed: int = 42):
        # Use temp directory that works on all platforms
        if db_path is None:
            import tempfile
            db_path = str(Path(tempfile.gettempdir()) / "query_gym.db")
        self.db_path = db_path
        self.seed = seed
        self.conn: Optional[sqlite3.Connection] = None
        
    def create_and_seed_db(self):
        """Create fresh database and seed with realistic e-commerce data."""
        # Remove old database if exists
        db_file = Path(self.db_path)
        if db_file.exists():
            db_file.unlink()
        
        # Create new connection (check_same_thread=False for async/multi-threaded environments)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Set random seed for reproducibility
        random.seed(self.seed)
        
        logger.info(f"Creating database at {self.db_path}")
        
        # Create tables
        self._create_tables()
        
        # Seed data
        self._seed_users(100_000)
        self._seed_orders(200_000)
        self._seed_order_items(500_000)
        
        # Commit and analyze
        self.conn.commit()
        self.conn.execute("ANALYZE")
        self.conn.commit()
        
        logger.info("Database created and seeded successfully")
    
    def _create_tables(self):
        """Create database schema."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                country TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Order items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
    
    def _seed_users(self, count: int):
        """Seed users table with realistic data."""
        logger.info(f"Seeding {count} users...")
        
        countries = ['US', 'IN', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'BR', 'MX']
        cursor = self.conn.cursor()
        
        batch_size = 10_000
        for batch_start in range(0, count, batch_size):
            users = []
            for i in range(batch_start, min(batch_start + batch_size, count)):
                email = f"user{i}@example.com"
                country = random.choice(countries)
                created_at = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                users.append((i + 1, email, country, created_at))
            
            cursor.executemany(
                "INSERT INTO users (id, email, country, created_at) VALUES (?, ?, ?, ?)",
                users
            )
        
        self.conn.commit()
        logger.info(f"Seeded {count} users")
    
    def _seed_orders(self, count: int):
        """Seed orders table with realistic data."""
        logger.info(f"Seeding {count} orders...")
        
        statuses = ['pending', 'completed', 'cancelled', 'refunded']
        cursor = self.conn.cursor()
        
        batch_size = 10_000
        for batch_start in range(0, count, batch_size):
            orders = []
            for i in range(batch_start, min(batch_start + batch_size, count)):
                user_id = random.randint(1, 100_000)
                total = round(random.uniform(10.0, 1000.0), 2)
                status = random.choice(statuses)
                created_at = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                orders.append((i + 1, user_id, total, status, created_at))
            
            cursor.executemany(
                "INSERT INTO orders (id, user_id, total, status, created_at) VALUES (?, ?, ?, ?, ?)",
                orders
            )
        
        self.conn.commit()
        logger.info(f"Seeded {count} orders")
    
    def _seed_order_items(self, count: int):
        """Seed order_items table with realistic data."""
        logger.info(f"Seeding {count} order items...")
        
        cursor = self.conn.cursor()
        
        batch_size = 10_000
        for batch_start in range(0, count, batch_size):
            items = []
            for i in range(batch_start, min(batch_start + batch_size, count)):
                order_id = random.randint(1, 200_000)
                product_id = random.randint(1, 10_000)
                quantity = random.randint(1, 5)
                items.append((i + 1, order_id, product_id, quantity))
            
            cursor.executemany(
                "INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (?, ?, ?, ?)",
                items
            )
        
        self.conn.commit()
        logger.info(f"Seeded {count} order items")
    
    def run_command(self, sql: str) -> Tuple[str, float, str]:
        """
        Execute SQL command safely and measure execution time.
        
        Returns:
            (output, execution_time_ms, query_plan)
        """
        if not self.conn:
            return "Error: Database not initialized", 0.0, ""
        
        sql = sql.strip()
        if not sql:
            return "Error: Empty command", 0.0, ""
        
        try:
            cursor = self.conn.cursor()
            
            # Handle CREATE INDEX
            if sql.upper().startswith("CREATE INDEX"):
                start = time.time()
                cursor.execute(sql)
                self.conn.commit()
                elapsed_ms = (time.time() - start) * 1000
                return f"Index created successfully ({elapsed_ms:.2f}ms)", elapsed_ms, ""
            
            # Handle DROP INDEX
            elif sql.upper().startswith("DROP INDEX"):
                start = time.time()
                cursor.execute(sql)
                self.conn.commit()
                elapsed_ms = (time.time() - start) * 1000
                return f"Index dropped successfully ({elapsed_ms:.2f}ms)", elapsed_ms, ""
            
            # Handle EXPLAIN QUERY PLAN
            elif sql.upper().startswith("EXPLAIN QUERY PLAN"):
                start = time.time()
                cursor.execute(sql)
                rows = cursor.fetchall()
                elapsed_ms = (time.time() - start) * 1000
                
                plan_lines = []
                for row in rows:
                    plan_lines.append(" | ".join(str(val) for val in row))
                
                plan = "\n".join(plan_lines) if plan_lines else "No plan available"
                return plan, elapsed_ms, plan
            
            # Handle ANALYZE
            elif sql.upper().startswith("ANALYZE"):
                start = time.time()
                cursor.execute(sql)
                self.conn.commit()
                elapsed_ms = (time.time() - start) * 1000
                return f"ANALYZE completed ({elapsed_ms:.2f}ms)", elapsed_ms, ""
            
            # Handle SELECT queries
            elif sql.upper().startswith("SELECT"):
                start = time.time()
                cursor.execute(sql)
                rows = cursor.fetchall()
                elapsed_ms = (time.time() - start) * 1000
                
                row_count = len(rows)
                output = f"Query returned {row_count} rows in {elapsed_ms:.2f}ms"
                
                # Get query plan
                plan_sql = f"EXPLAIN QUERY PLAN {sql}"
                cursor.execute(plan_sql)
                plan_rows = cursor.fetchall()
                plan_lines = [" | ".join(str(val) for val in row) for row in plan_rows]
                plan = "\n".join(plan_lines) if plan_lines else ""
                
                return output, elapsed_ms, plan
            
            # Unsupported command
            else:
                return f"Error: Unsupported command type. Use CREATE INDEX, EXPLAIN QUERY PLAN, ANALYZE, or SELECT.", 0.0, ""
        
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            return f"Error: {str(e)}", 0.0, ""
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return f"Error: {str(e)}", 0.0, ""
    
    def measure_query_time(self, sql: str) -> float:
        """Measure execution time of a SELECT query in milliseconds."""
        if not self.conn:
            return 0.0
        
        try:
            cursor = self.conn.cursor()
            start = time.time()
            cursor.execute(sql)
            cursor.fetchall()  # Fetch all to ensure full execution
            elapsed_ms = (time.time() - start) * 1000
            return elapsed_ms
        except Exception as e:
            logger.error(f"Error measuring query time: {e}")
            return 0.0
    
    def get_query_plan(self, sql: str) -> str:
        """Get EXPLAIN QUERY PLAN output for a query."""
        if not self.conn:
            return ""
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
            rows = cursor.fetchall()
            plan_lines = [" | ".join(str(val) for val in row) for row in rows]
            return "\n".join(plan_lines) if plan_lines else ""
        except Exception as e:
            logger.error(f"Error getting query plan: {e}")
            return ""
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
