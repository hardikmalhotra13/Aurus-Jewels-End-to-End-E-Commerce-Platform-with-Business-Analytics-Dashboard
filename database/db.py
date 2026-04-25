"""
database/db.py — MySQL connection helpers for Aurus Jewels
"""
import mysql.connector
from mysql.connector import pooling
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name    = "aurus_pool",
                pool_size    = 5,
                host         = config.DB_HOST,
                port         = config.DB_PORT,
                user         = config.DB_USER,
                password     = config.DB_PASSWORD,
                database     = config.DB_NAME,
                charset      = "utf8mb4",
                collation    = "utf8mb4_unicode_ci",
                autocommit   = False,
            )
        except Exception as e:
            st.error(f"⚠️ Database connection failed: {e}")
            return None
    return _pool


def get_connection():
    pool = _get_pool()
    if pool:
        return pool.get_connection()
    return None


def execute_query(sql: str, params=None) -> list:
    """SELECT — returns list of row dicts."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return rows
    except Exception as e:
        st.error(f"Query error: {e}")
        return []
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def execute_one(sql: str, params=None):
    """SELECT ONE — returns single row dict or None."""
    rows = execute_query(sql, params)
    return rows[0] if rows else None


def execute_write(sql: str, params=None):
    """INSERT / UPDATE / DELETE — returns lastrowid or rowcount."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid if cur.lastrowid else cur.rowcount
    except Exception as e:
        conn.rollback()
        st.error(f"Write error: {e}")
        return None
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def execute_many(sql: str, params_list: list) -> bool:
    """Bulk INSERT — returns True on success."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.executemany(sql, params_list)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Bulk write error: {e}")
        return False
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass