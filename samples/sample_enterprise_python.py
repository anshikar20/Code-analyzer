#!/usr/bin/env python3
"""
Enterprise User Management & Payment Platform
CodePulse AI — Sample File for Static Analysis Testing
Lines: ~2100 | Language: Python 3.10+
Contains: intentional security flaws, type errors, dead code, SQL injection,
          hardcoded secrets, improper exception handling, performance issues
"""

# ─── Standard Library ─────────────────────────────────────────────────────────
import os
import re
import sys
import json
import time
import logging
import hashlib
import sqlite3
import smtplib
import threading
import subprocess
import collections
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from functools import wraps, lru_cache
from abc import ABC, abstractmethod

# ─── Third-party (simulated) ──────────────────────────────────────────────────
# NOTE: These would be real imports in production
# import fastapi, sqlalchemy, redis, celery, stripe

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# ❌ SECURITY ISSUE: Hardcoded secrets — never do this in production!
# ══════════════════════════════════════════════════════════════════════════════
DATABASE_URL = "sqlite:///enterprise.db"
SECRET_KEY = "super_secret_key_12345_do_not_share"
JWT_SECRET = "jwt_secret_password_hardcoded"
STRIPE_SECRET_KEY = "sk_live_abc123def456_hardcoded"
SMTP_PASSWORD = "smtp_password_1234"
ADMIN_PASSWORD = "admin123"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
REDIS_URL = "redis://:hardcoded_redis_password@localhost:6379"

# ══════════════════════════════════════════════════════════════════════════════
# Enumerations
# ══════════════════════════════════════════════════════════════════════════════
class UserRole(Enum):
    ADMIN = auto()
    MODERATOR = auto()
    USER = auto()
    GUEST = auto()

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class OrderStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# ══════════════════════════════════════════════════════════════════════════════
# Data Classes / Models
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

    def validate(self) -> bool:
        # ❌ DEAD CODE: this regex never matches zip codes properly
        zip_regex = r"^\d{5}-\d{4}$"  # Only matches extended ZIP, not standard
        return bool(re.match(zip_regex, self.zip_code))

    def to_dict(self) -> Dict[str, str]:
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
        }


@dataclass
class User:
    id: int
    username: str
    email: str
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    address: Optional[Address] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # ❌ TYPE ERROR: comparing str to int
        if self.id == "0":
            raise ValueError("Invalid user ID")

    def get_display_name(self) -> str:
        return f"{self.username} ({self.email})"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.name,
            "is_active": self.is_active,
        }


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int
    category: str
    sku: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_deleted: bool = False

    def apply_discount(self, percent: float) -> float:
        # ❌ TYPE ERROR: no return type annotation inconsistency
        if percent < 0 or percent > 100:
            return self.price  # silently ignores invalid input
        return self.price * (1 - percent / 100)

    def is_in_stock(self) -> bool:
        return self.stock > 0

    def reserve(self, quantity: int) -> bool:
        if quantity <= 0:
            return False
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False


@dataclass
class OrderItem:
    product: Product
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class Order:
    id: int
    user: User
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    shipping_address: Optional[Address] = None
    notes: str = ""

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def add_item(self, product: Product, quantity: int) -> None:
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self.items.append(OrderItem(product, quantity, product.price))

    def submit(self) -> bool:
        if not self.items:
            return False
        if self.status != OrderStatus.DRAFT:
            return False
        self.status = OrderStatus.SUBMITTED
        return True


# ══════════════════════════════════════════════════════════════════════════════
# Database Layer — RAW SQL (intentional vulnerabilities for testing)
# ══════════════════════════════════════════════════════════════════════════════
class DatabaseManager:
    """Manages raw SQLite connections. Intentionally uses string formatting for SQL."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._conn = None
        return cls._instance

    def connect(self, db_path: str = "enterprise.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'USER',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                failed_login_attempts INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                category TEXT,
                sku TEXT UNIQUE,
                description TEXT DEFAULT '',
                is_deleted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'draft',
                total REAL DEFAULT 0.0,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self._conn.commit()

    # ❌ SECURITY: SQL Injection vulnerability — user input directly interpolated!
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        cursor = self._conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}'"
        cursor.execute(query)
        row = cursor.fetchone()
        return dict(row) if row else None

    # ✅ SAFE: Parameterized query (contrast for testing)
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ❌ SECURITY: SQL Injection in search
    def search_products(self, query: str) -> List[Dict]:
        cursor = self._conn.cursor()
        sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' AND is_deleted = 0"
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    # ❌ SECURITY: SQL Injection in order filter
    def get_orders_by_status(self, status: str, user_id: str) -> List[Dict]:
        cursor = self._conn.cursor()
        sql = f"SELECT * FROM orders WHERE status = '{status}' AND user_id = {user_id}"
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def create_user(self, username: str, email: str, password_hash: str, role: str = "USER") -> int:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role)
        )
        self._conn.commit()
        return cursor.lastrowid

    def update_user_last_login(self, user_id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), user_id)
        )
        self._conn.commit()

    def log_audit(self, user_id: Optional[int], action: str, details: str, ip: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
            (user_id, action, details, ip)
        )
        self._conn.commit()

    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        cursor = self._conn.cursor()
        if include_inactive:
            cursor.execute("SELECT * FROM users")
        else:
            cursor.execute("SELECT * FROM users WHERE is_active = 1")
        return [dict(row) for row in cursor.fetchall()]

    def bulk_insert_products(self, products: List[Dict]) -> int:
        cursor = self._conn.cursor()
        inserted = 0
        for p in products:
            try:
                cursor.execute(
                    "INSERT INTO products (name, price, stock, category, sku) VALUES (?, ?, ?, ?, ?)",
                    (p["name"], p["price"], p.get("stock", 0), p.get("category", ""), p["sku"])
                )
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # ❌ QUALITY: Silently swallowing exceptions
        self._conn.commit()
        return inserted

    def delete_product(self, product_id: int) -> bool:
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE products SET is_deleted = 1 WHERE id = ?",
            (product_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ══════════════════════════════════════════════════════════════════════════════
# Authentication Service
# ══════════════════════════════════════════════════════════════════════════════
class AuthService:
    """Handles authentication, password hashing, and session tokens."""

    MAX_LOGIN_ATTEMPTS = 5
    SESSION_DURATION_HOURS = 24

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    # ❌ SECURITY: MD5 is cryptographically broken — use bcrypt/argon2!
    def hash_password(self, password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    def verify_password(self, plain: str, hashed: str) -> bool:
        # ❌ SECURITY: MD5 comparison (same issue)
        return hashlib.md5(plain.encode()).hexdigest() == hashed

    def generate_token(self, user_id: int) -> str:
        # ❌ SECURITY: Token is just MD5(user_id + secret) — trivially predictable
        raw = f"{user_id}:{SECRET_KEY}:{time.time()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def login(self, username: str, password: str, ip_address: str = "0.0.0.0") -> Optional[str]:
        user = self.db.get_user_by_username(username)
        if not user:
            self.db.log_audit(None, "LOGIN_FAILED", f"Unknown user: {username}", ip_address)
            return None

        if user["failed_login_attempts"] >= self.MAX_LOGIN_ATTEMPTS:
            logger.warning(f"Account locked: {username}")
            return None

        if not self.verify_password(password, user["password_hash"]):
            # Update failed attempts
            cursor = self.db._conn.cursor()
            cursor.execute(
                "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = ?",
                (user["id"],)
            )
            self.db._conn.commit()
            self.db.log_audit(user["id"], "LOGIN_FAILED", "Bad password", ip_address)
            return None

        token = self.generate_token(user["id"])
        expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_DURATION_HOURS)

        with self._lock:
            self._sessions[token] = {
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "expires_at": expires_at,
            }

        # Reset failed attempts on success
        cursor = self.db._conn.cursor()
        cursor.execute(
            "UPDATE users SET failed_login_attempts = 0, last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), user["id"])
        )
        self.db._conn.commit()
        self.db.log_audit(user["id"], "LOGIN_SUCCESS", "", ip_address)
        return token

    def validate_token(self, token: str) -> Optional[Dict]:
        with self._lock:
            session = self._sessions.get(token)
        if not session:
            return None
        if datetime.utcnow() > session["expires_at"]:
            self.logout(token)
            return None
        return session

    def logout(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def register_user(self, username: str, email: str, password: str, role: str = "USER") -> int:
        # ❌ QUALITY: No input validation (empty username, invalid email, weak password)
        hashed = self.hash_password(password)
        user_id = self.db.create_user(username, email, hashed, role)
        logger.info(f"Registered new user: {username} (ID: {user_id})")
        return user_id

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return False
        if not self.verify_password(old_password, user["password_hash"]):
            return False
        # ❌ QUALITY: No password strength enforcement
        new_hash = self.hash_password(new_password)
        cursor = self.db._conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id)
        )
        self.db._conn.commit()
        return True

    # ❌ DEAD CODE: this method is never called anywhere
    def _cleanup_expired_sessions(self) -> int:
        now = datetime.utcnow()
        expired = [t for t, s in self._sessions.items() if now > s["expires_at"]]
        for t in expired:
            del self._sessions[t]
        return len(expired)


# ══════════════════════════════════════════════════════════════════════════════
# Product Service
# ══════════════════════════════════════════════════════════════════════════════
class ProductService:
    """Business logic for product management."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        # ❌ PERFORMANCE: In-memory cache with no TTL or size limit
        self._cache: Dict[int, Dict] = {}

    def get_product(self, product_id: int) -> Optional[Dict]:
        if product_id in self._cache:
            return self._cache[product_id]
        cursor = self.db._conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ? AND is_deleted = 0", (product_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            self._cache[product_id] = result
            return result
        return None

    def create_product(self, data: Dict) -> int:
        required = ["name", "price", "sku"]
        for field_name in required:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        # ❌ TYPE ERROR: price could be a string from JSON, no explicit cast
        price = data["price"]  # Should be: float(data["price"])
        cursor = self.db._conn.cursor()
        cursor.execute(
            """INSERT INTO products (name, price, stock, category, sku, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data["name"], price,
                data.get("stock", 0),
                data.get("category", ""),
                data["sku"],
                data.get("description", ""),
            )
        )
        self.db._conn.commit()
        product_id = cursor.lastrowid
        logger.info(f"Product created: {data['name']} (ID: {product_id})")
        return product_id

    def update_stock(self, product_id: int, delta: int) -> bool:
        """Add or subtract from product stock."""
        cursor = self.db._conn.cursor()
        cursor.execute(
            "UPDATE products SET stock = MAX(0, stock + ?) WHERE id = ? AND is_deleted = 0",
            (delta, product_id)
        )
        self.db._conn.commit()
        if product_id in self._cache:
            del self._cache[product_id]
        return cursor.rowcount > 0

    def apply_bulk_discount(self, category: str, percent: float) -> int:
        """Apply a percentage discount to all products in a category."""
        if not (0 < percent <= 100):
            raise ValueError("Discount must be between 0 and 100")
        cursor = self.db._conn.cursor()
        # ❌ SECURITY: Category not parameterized (SQL injection possible)
        cursor.execute(
            f"UPDATE products SET price = price * {1 - percent / 100} WHERE category = '{category}'"
        )
        self.db._conn.commit()
        return cursor.rowcount

    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        cursor = self.db._conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE stock <= ? AND is_deleted = 0 ORDER BY stock ASC",
            (threshold,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_products_by_category(self, category: str) -> List[Dict]:
        return self.db.search_products("")  # ❌ BUG: ignores category, searches all!

    @lru_cache(maxsize=128)
    def get_price_history(self, product_id: int) -> List[float]:
        # ❌ QUALITY: LRU cache on mutable database data; stale cache issue
        return []  # Stub — not implemented

    def export_products_csv(self) -> str:
        """Export all products to CSV format."""
        cursor = self.db._conn.cursor()
        cursor.execute("SELECT * FROM products WHERE is_deleted = 0")
        rows = cursor.fetchall()
        lines = ["id,name,price,stock,category,sku"]
        for row in rows:
            # ❌ QUALITY: No escaping of commas in product names
            lines.append(f"{row['id']},{row['name']},{row['price']},{row['stock']},{row['category']},{row['sku']}")
        return "\n".join(lines)

    # ❌ DEAD CODE: Never called, obsolete method
    def _old_get_product_by_sku(self, sku):
        for pid, prod in self._cache.items():
            if prod.get("sku") == sku:
                return prod
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Order Service
# ══════════════════════════════════════════════════════════════════════════════
class OrderService:
    """Business logic for order lifecycle management."""

    def __init__(self, db: DatabaseManager, product_svc: ProductService):
        self.db = db
        self.product_svc = product_svc
        self._order_events: List[Dict] = []

    def create_order(self, user_id: int) -> int:
        cursor = self.db._conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id) VALUES (?)",
            (user_id,)
        )
        self.db._conn.commit()
        return cursor.lastrowid

    def add_item_to_order(self, order_id: int, product_id: int, quantity: int) -> bool:
        product = self.product_svc.get_product(product_id)
        if not product:
            return False
        if product["stock"] < quantity:
            logger.warning(f"Insufficient stock for product {product_id}")
            return False

        cursor = self.db._conn.cursor()
        # Check if item already in order
        cursor.execute(
            "SELECT * FROM order_items WHERE order_id = ? AND product_id = ?",
            (order_id, product_id)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE order_items SET quantity = quantity + ? WHERE order_id = ? AND product_id = ?",
                (quantity, order_id, product_id)
            )
        else:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, product["price"])
            )

        # Reserve stock
        self.product_svc.update_stock(product_id, -quantity)
        self.db._conn.commit()
        return True

    def submit_order(self, order_id: int) -> bool:
        cursor = self.db._conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE id = ? AND status = 'draft'",
            (order_id,)
        )
        order = cursor.fetchone()
        if not order:
            return False

        # Calculate total
        cursor.execute(
            """SELECT SUM(quantity * unit_price) as total
               FROM order_items WHERE order_id = ?""",
            (order_id,)
        )
        total_row = cursor.fetchone()
        total = total_row["total"] if total_row["total"] else 0.0

        cursor.execute(
            "UPDATE orders SET status = 'submitted', total = ? WHERE id = ?",
            (total, order_id)
        )
        self.db._conn.commit()

        self._order_events.append({
            "order_id": order_id,
            "event": "submitted",
            "timestamp": datetime.utcnow().isoformat(),
            "total": total,
        })
        return True

    def cancel_order(self, order_id: int, user_id: int) -> bool:
        cursor = self.db._conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id)
        )
        order = cursor.fetchone()
        if not order:
            return False

        if order["status"] in ("shipped", "delivered"):
            return False

        # Restore stock
        cursor.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ?",
            (order_id,)
        )
        for item in cursor.fetchall():
            self.product_svc.update_stock(item["product_id"], item["quantity"])

        cursor.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ?",
            (order_id,)
        )
        self.db._conn.commit()
        return True

    def get_order_summary(self, order_id: int) -> Optional[Dict]:
        cursor = self.db._conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            return None

        cursor.execute("""
            SELECT oi.*, p.name, p.sku
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = [dict(row) for row in cursor.fetchall()]

        return {
            "order": dict(order),
            "items": items,
            "item_count": len(items),
        }

    # ❌ PERFORMANCE: N+1 query problem — fetches orders one by one
    def get_user_order_history(self, user_id: int) -> List[Dict]:
        cursor = self.db._conn.cursor()
        cursor.execute("SELECT id FROM orders WHERE user_id = ?", (user_id,))
        order_ids = [row["id"] for row in cursor.fetchall()]
        results = []
        for oid in order_ids:
            summary = self.get_order_summary(oid)
            if summary:
                results.append(summary)
        return results


# ══════════════════════════════════════════════════════════════════════════════
# Payment Service
# ══════════════════════════════════════════════════════════════════════════════
class PaymentService:
    """Handles payment processing and refunds."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        # ❌ SECURITY: Using hardcoded API key
        self.api_key = STRIPE_SECRET_KEY
        self._payments: Dict[str, Dict] = {}

    def charge_card(self, order_id: int, amount: float, card_number: str, cvv: str) -> Dict:
        # ❌ SECURITY: CVV and card number stored in plaintext in logs!
        logger.info(f"Processing payment for order {order_id}: card={card_number}, cvv={cvv}")

        # ❌ SECURITY: Writing sensitive card data to a file
        with open("payment_log.txt", "a") as f:
            f.write(f"{datetime.utcnow()}: Order {order_id}, Card: {card_number}, CVV: {cvv}, Amount: {amount}\n")

        # Simulate payment (would call Stripe API in real code)
        payment_id = hashlib.md5(f"{order_id}{time.time()}".encode()).hexdigest()

        self._payments[payment_id] = {
            "order_id": order_id,
            "amount": amount,
            "status": PaymentStatus.COMPLETED.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return {"payment_id": payment_id, "status": "success", "amount": amount}

    def refund_payment(self, payment_id: str, reason: str = "") -> bool:
        if payment_id not in self._payments:
            return False
        self._payments[payment_id]["status"] = PaymentStatus.REFUNDED.value
        self._payments[payment_id]["refund_reason"] = reason
        return True

    def get_payment_status(self, payment_id: str) -> Optional[str]:
        payment = self._payments.get(payment_id)
        return payment["status"] if payment else None

    # ❌ DEAD CODE: never called
    def _validate_card_luhn(self, card_number: str) -> bool:
        digits = [int(d) for d in card_number.replace(" ", "")]
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits) % 10 == 0


# ══════════════════════════════════════════════════════════════════════════════
# Email Service
# ══════════════════════════════════════════════════════════════════════════════
class EmailService:
    """Handles transactional email sending via SMTP."""

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "app@company.com"
    # ❌ SECURITY: Password stored directly in code
    SMTP_PASS = SMTP_PASSWORD

    def __init__(self):
        self._sent: List[Dict] = []
        self._lock = threading.Lock()

    def send_email(self, to: str, subject: str, body: str) -> bool:
        try:
            # ❌ QUALITY: Creating new SMTP connection per email (should pool)
            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(self.SMTP_USER, self.SMTP_PASS)
                message = f"From: {self.SMTP_USER}\nTo: {to}\nSubject: {subject}\n\n{body}"
                smtp.sendmail(self.SMTP_USER, to, message)
            with self._lock:
                self._sent.append({"to": to, "subject": subject, "sent_at": datetime.utcnow().isoformat()})
            return True
        except Exception as e:
            # ❌ QUALITY: Generic exception catch, no specific handling
            logger.error(f"Email failed: {e}")
            return False

    def send_order_confirmation(self, user_email: str, order_id: int, total: float) -> bool:
        subject = f"Order Confirmation #{order_id}"
        body = f"""
Dear Customer,

Your order #{order_id} has been confirmed.
Total: ${total:.2f}

Thank you for shopping with us!
        """.strip()
        return self.send_email(user_email, subject, body)

    def send_password_reset(self, user_email: str, reset_token: str) -> bool:
        subject = "Password Reset Request"
        # ❌ SECURITY: Token sent in plain HTTP link
        body = f"""
Click the link to reset your password:
http://myapp.com/reset?token={reset_token}

This link expires in 1 hour.
        """.strip()
        return self.send_email(user_email, subject, body)

    def send_admin_alert(self, message: str) -> bool:
        return self.send_email("admin@company.com", "ALERT", message)

    def get_sent_count(self) -> int:
        return len(self._sent)


# ══════════════════════════════════════════════════════════════════════════════
# File Upload Service
# ══════════════════════════════════════════════════════════════════════════════
class FileUploadService:
    """Handles file uploads from users."""

    UPLOAD_DIR = Path("uploads")
    # ❌ SECURITY: No restriction on allowed file types
    MAX_FILE_SIZE_MB = 100

    def __init__(self):
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    def save_file(self, filename: str, content: bytes, user_id: int) -> str:
        # ❌ SECURITY: No path traversal prevention — could overwrite system files!
        dest = self.UPLOAD_DIR / filename
        with open(dest, "wb") as f:
            f.write(content)
        logger.info(f"User {user_id} uploaded: {filename}")
        return str(dest)

    def get_file_path(self, filename: str) -> Path:
        # ❌ SECURITY: Path traversal: filename could be "../../../etc/passwd"
        return self.UPLOAD_DIR / filename

    def delete_file(self, filename: str, user_id: int) -> bool:
        path = self.get_file_path(filename)
        if path.exists():
            path.unlink()
            return True
        return False

    def process_csv_import(self, filepath: str) -> List[Dict]:
        """Parse a CSV product import file."""
        results = []
        # ❌ SECURITY: No validation of file type before opening
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    results.append({
                        "name": parts[0],
                        "price": parts[1],  # ❌ TYPE: string, should be float
                        "stock": parts[2],  # ❌ TYPE: string, should be int
                        "sku": parts[3],
                    })
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
        except Exception as e:
            logger.error(f"CSV parse error: {e}")
        return results

    # ❌ SECURITY: Executing user-provided filenames as shell commands!
    def get_file_info(self, filename: str) -> str:
        result = subprocess.run(
            f"file uploads/{filename}",
            shell=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    # ❌ DEAD CODE: method is never used
    def _compress_file(self, filepath: str) -> str:
        import gzip
        compressed_path = filepath + ".gz"
        with open(filepath, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                f_out.write(f_in.read())
        return compressed_path


# ══════════════════════════════════════════════════════════════════════════════
# Admin Service
# ══════════════════════════════════════════════════════════════════════════════
class AdminService:
    """Administrative operations for managing the platform."""

    def __init__(self, db: DatabaseManager, auth: AuthService, email: EmailService):
        self.db = db
        self.auth = auth
        self.email = email

    def get_platform_stats(self) -> Dict:
        cursor = self.db._conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM orders")
        total_orders = cursor.fetchone()["count"]

        cursor.execute("SELECT SUM(total) as revenue FROM orders WHERE status = 'delivered'")
        revenue_row = cursor.fetchone()
        revenue = revenue_row["revenue"] or 0.0

        cursor.execute("SELECT COUNT(*) as count FROM products WHERE is_deleted = 0 AND stock = 0")
        out_of_stock = cursor.fetchone()["count"]

        return {
            "active_users": active_users,
            "total_orders": total_orders,
            "total_revenue": revenue,
            "out_of_stock_products": out_of_stock,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def bulk_deactivate_users(self, user_ids: List[int]) -> int:
        cursor = self.db._conn.cursor()
        deactivated = 0
        for uid in user_ids:
            cursor.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (uid,)
            )
            deactivated += cursor.rowcount
        self.db._conn.commit()
        logger.warning(f"Admin deactivated {deactivated} users: {user_ids}")
        return deactivated

    def export_audit_logs(self, days: int = 30) -> List[Dict]:
        cursor = self.db._conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute(
            "SELECT * FROM audit_logs WHERE created_at >= ? ORDER BY created_at DESC",
            (since,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def reset_user_password(self, admin_token: str, target_user_id: int, new_password: str) -> bool:
        session = self.auth.validate_token(admin_token)
        if not session or session["role"] != "ADMIN":
            return False

        new_hash = self.auth.hash_password(new_password)
        cursor = self.db._conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, target_user_id)
        )
        self.db._conn.commit()

        # ❌ SECURITY: Sending plain-text new password in email
        user = self.db.get_user_by_id(target_user_id)
        if user:
            self.email.send_email(
                user["email"],
                "Your password was reset",
                f"Your new password is: {new_password}"  # ❌ Never send plaintext passwords!
            )
        return True

    def run_maintenance(self) -> Dict:
        """Perform routine maintenance tasks."""
        results = {}

        # Clean old sessions
        expired_sessions = self.auth._cleanup_expired_sessions()
        results["expired_sessions_cleaned"] = expired_sessions

        # ❌ SECURITY: Running shell command to clean temp files
        result = subprocess.run(
            "rm -rf /tmp/app_cache/*",
            shell=True,
            capture_output=True,
        )
        results["cache_cleaned"] = result.returncode == 0

        return results


# ══════════════════════════════════════════════════════════════════════════════
# Report Generator
# ══════════════════════════════════════════════════════════════════════════════
class ReportGenerator:
    """Generates business intelligence reports."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def sales_report(self, start_date: str, end_date: str) -> Dict:
        cursor = self.db._conn.cursor()
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as order_count,
                SUM(total) as revenue
            FROM orders
            WHERE status IN ('submitted', 'processing', 'shipped', 'delivered')
              AND created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date))

        rows = cursor.fetchall()
        total_revenue = sum(r["revenue"] for r in rows if r["revenue"])

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_orders": sum(r["order_count"] for r in rows),
            "total_revenue": total_revenue,
            "daily_breakdown": [dict(r) for r in rows],
        }

    def user_retention_report(self) -> Dict:
        """Calculate user retention metrics."""
        cursor = self.db._conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM users")
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as active
            FROM orders
            WHERE created_at >= DATE('now', '-30 days')
        """)
        active_30d = cursor.fetchone()["active"]

        retention_rate = (active_30d / total * 100) if total > 0 else 0.0

        return {
            "total_users": total,
            "active_last_30_days": active_30d,
            "retention_rate": round(retention_rate, 2),
        }

    def top_products_report(self, limit: int = 10) -> List[Dict]:
        cursor = self.db._conn.cursor()
        cursor.execute("""
            SELECT
                p.id, p.name, p.category,
                SUM(oi.quantity) as units_sold,
                SUM(oi.quantity * oi.unit_price) as revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY revenue DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ❌ PERFORMANCE: Loading all orders into memory at once
    def full_data_export(self) -> Dict:
        cursor = self.db._conn.cursor()
        cursor.execute("SELECT * FROM orders")
        all_orders = [dict(r) for r in cursor.fetchall()]  # Could be millions of rows!

        cursor.execute("SELECT * FROM users")
        all_users = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM products")
        all_products = [dict(r) for r in cursor.fetchall()]

        return {
            "orders": all_orders,
            "users": all_users,
            "products": all_products,
            "exported_at": datetime.utcnow().isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Cache Layer
# ══════════════════════════════════════════════════════════════════════════════
class SimpleCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Tuple[Any, datetime]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._store:
                value, expires_at = self._store[key]
                if datetime.utcnow() < expires_at:
                    self.hits += 1
                    return value
                else:
                    del self._store[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        with self._lock:
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.hits / total * 100:.1f}%" if total > 0 else "0%",
            "size": len(self._store),
        }

    # ❌ DEAD CODE: Never called from anywhere
    def _evict_oldest(self, count: int = 10) -> None:
        with self._lock:
            if len(self._store) <= count:
                return
            sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
            for key in sorted_keys[:count]:
                del self._store[key]


# ══════════════════════════════════════════════════════════════════════════════
# Background Task Runner
# ══════════════════════════════════════════════════════════════════════════════
class BackgroundTaskRunner:
    """Simple thread-based background task scheduler."""

    def __init__(self):
        self._tasks: Dict[str, threading.Thread] = {}
        self._running = False
        self._results: Dict[str, Any] = {}

    def submit(self, name: str, fn, *args, **kwargs) -> None:
        if name in self._tasks and self._tasks[name].is_alive():
            logger.warning(f"Task '{name}' already running, skipping")
            return

        def wrapper():
            try:
                result = fn(*args, **kwargs)
                self._results[name] = {"status": "success", "result": result}
            except Exception as e:
                # ❌ QUALITY: Broad exception catch without re-raise
                self._results[name] = {"status": "error", "error": str(e)}

        thread = threading.Thread(target=wrapper, name=name, daemon=True)
        self._tasks[name] = thread
        thread.start()
        logger.info(f"Background task started: {name}")

    def get_result(self, name: str) -> Optional[Dict]:
        return self._results.get(name)

    def is_running(self, name: str) -> bool:
        thread = self._tasks.get(name)
        return thread is not None and thread.is_alive()

    def wait_all(self, timeout: float = 30.0) -> None:
        for name, thread in self._tasks.items():
            thread.join(timeout=timeout)

    # ❌ PERFORMANCE: Blocking sleep in main thread for polling
    def wait_for(self, name: str, poll_interval: float = 0.5) -> Optional[Dict]:
        while self.is_running(name):
            time.sleep(poll_interval)  # Should use event/condition variable
        return self.get_result(name)


# ══════════════════════════════════════════════════════════════════════════════
# REST API Handler (Simulated — no actual HTTP framework)
# ══════════════════════════════════════════════════════════════════════════════
class APIRouter:
    """Simple route dispatcher simulating a REST API framework."""

    def __init__(self):
        self._routes: Dict[str, Dict[str, Any]] = {}

    def route(self, method: str, path: str):
        def decorator(fn):
            key = f"{method.upper()}:{path}"
            self._routes[key] = fn
            return fn
        return decorator

    def dispatch(self, method: str, path: str, body: Dict = None, headers: Dict = None) -> Dict:
        key = f"{method.upper()}:{path}"
        handler = self._routes.get(key)
        if not handler:
            return {"status": 404, "error": "Not Found"}
        try:
            result = handler(body=body, headers=headers)
            return {"status": 200, "data": result}
        except ValueError as e:
            return {"status": 400, "error": str(e)}
        except PermissionError as e:
            return {"status": 403, "error": str(e)}
        except Exception as e:
            logger.error(f"API error: {e}")
            return {"status": 500, "error": "Internal Server Error"}


# ══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ══════════════════════════════════════════════════════════════════════════════
def paginate(items: list, page: int, per_page: int) -> Dict:
    """Paginate a list of items."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    }


def validate_email(email: str) -> bool:
    # ❌ QUALITY: Overly simplistic email validation
    return "@" in email and "." in email


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate."""
    return str(value).strip()[:max_length]


def generate_sku(name: str, category: str, counter: int) -> str:
    prefix = (category[:3] + name[:3]).upper().replace(" ", "")
    return f"{prefix}-{counter:06d}"


def format_currency(amount: float, currency: str = "USD") -> str:
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry a function on exception."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


# ❌ DEAD CODE: Unused import and function
def _unused_json_pretty_print(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)

# ❌ DEAD CODE: Never called
_LEGACY_TAX_RATES = {
    "CA": 0.0725,
    "NY": 0.045,
    "TX": 0.0625,
}


def calculate_tax(amount: float, state: str) -> float:
    rate = _LEGACY_TAX_RATES.get(state, 0.0)
    return amount * rate


# ══════════════════════════════════════════════════════════════════════════════
# Application Bootstrap
# ══════════════════════════════════════════════════════════════════════════════
class Application:
    """Main application container — dependency injection root."""

    def __init__(self, db_path: str = "enterprise.db"):
        self.db = DatabaseManager()
        self.db.connect(db_path)

        self.auth = AuthService(self.db)
        self.products = ProductService(self.db)
        self.orders = OrderService(self.db, self.products)
        self.payments = PaymentService(self.db)
        self.email = EmailService()
        self.files = FileUploadService()
        self.admin = AdminService(self.db, self.auth, self.email)
        self.reports = ReportGenerator(self.db)
        self.cache = SimpleCache()
        self.tasks = BackgroundTaskRunner()
        self.router = APIRouter()

        self._register_routes()
        logger.info("Application initialized")

    def _register_routes(self) -> None:
        """Register all API routes."""
        @self.router.route("POST", "/auth/login")
        def login(body=None, headers=None):
            if not body:
                raise ValueError("Request body required")
            token = self.auth.login(
                body.get("username", ""),
                body.get("password", ""),
                headers.get("X-Forwarded-For", "0.0.0.0") if headers else "0.0.0.0"
            )
            if not token:
                raise PermissionError("Invalid credentials")
            return {"token": token}

        @self.router.route("POST", "/auth/register")
        def register(body=None, headers=None):
            if not body:
                raise ValueError("Request body required")
            user_id = self.auth.register_user(
                body.get("username", ""),
                body.get("email", ""),
                body.get("password", ""),
            )
            return {"user_id": user_id, "message": "Registration successful"}

        @self.router.route("GET", "/products")
        def list_products(body=None, headers=None):
            cursor = self.db._conn.cursor()
            cursor.execute("SELECT * FROM products WHERE is_deleted = 0")
            return [dict(r) for r in cursor.fetchall()]

        @self.router.route("POST", "/products")
        def create_product(body=None, headers=None):
            product_id = self.products.create_product(body or {})
            return {"product_id": product_id}

        @self.router.route("GET", "/admin/stats")
        def admin_stats(body=None, headers=None):
            return self.admin.get_platform_stats()

    def run_sample_scenario(self) -> None:
        """Demonstrate the full system flow."""
        print("\n=== CodePulse AI — Enterprise Sample Scenario ===\n")

        # Register users
        admin_id = self.auth.register_user("admin", "admin@corp.com", ADMIN_PASSWORD, "ADMIN")
        user_id = self.auth.register_user("alice", "alice@example.com", "alice_pass_123")
        print(f"Users created: admin ID={admin_id}, alice ID={user_id}")

        # Create products
        prod1 = self.products.create_product({"name": "Widget Pro", "price": 29.99, "stock": 100, "sku": "WGT-001", "category": "Electronics"})
        prod2 = self.products.create_product({"name": "Gadget Ultra", "price": 99.99, "stock": 50, "sku": "GDG-001", "category": "Electronics"})
        print(f"Products created: IDs {prod1}, {prod2}")

        # Login
        token = self.auth.login("alice", "alice_pass_123")
        print(f"Alice logged in, token: {token[:16]}...")

        # Create order
        order_id = self.orders.create_order(user_id)
        self.orders.add_item_to_order(order_id, prod1, 2)
        self.orders.add_item_to_order(order_id, prod2, 1)
        summary = self.orders.get_order_summary(order_id)
        print(f"Order #{order_id} created, total: {format_currency(summary['order']['total'])}")

        # Submit order
        self.orders.submit_order(order_id)
        print("Order submitted")

        # Payment (intentionally logging card details — vulnerability demo)
        payment = self.payments.charge_card(order_id, summary['order']['total'], "4111111111111111", "123")
        print(f"Payment processed: {payment['payment_id'][:16]}...")

        # Stats
        stats = self.admin.get_platform_stats()
        print(f"Platform stats: {json.dumps(stats, indent=2)}")

        # Reports
        report = self.reports.user_retention_report()
        print(f"Retention: {report}")


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    app = Application()
    app.run_sample_scenario()

    print("\nAll done! Upload this file to CodePulse AI to see the analysis results.")
