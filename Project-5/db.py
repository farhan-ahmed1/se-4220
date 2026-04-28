"""Tiny MySQL helper. Each request gets its own connection (simplest model;
we are not optimizing for concurrency in a class demo)."""

import os
import mysql.connector
from contextlib import contextmanager


def _connect():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOSTNAME", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USERNAME", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "classifieds_db"),
        autocommit=False,
    )


@contextmanager
def get_cursor(dictionary=True, commit=False):
    """Yields a cursor and cleans up the connection.

    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=dictionary)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


def query_all(sql, params=None):
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def query_one(sql, params=None):
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE; returns lastrowid."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid
