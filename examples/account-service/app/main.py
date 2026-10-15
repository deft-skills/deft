"""Minimal account service used as the existing system of the running example.

Users can register and log in. Password reset is the feature request.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

DB_PATH = os.environ.get("APP_DB", "app.db")

app = FastAPI(title="Accounts")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS users ("
                 "id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                 "salt TEXT NOT NULL, password_hash TEXT NOT NULL)")
    try:
        yield conn
    finally:
        conn.close()


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


class Credentials(BaseModel):
    email: EmailStr
    password: str


@app.post("/users", status_code=201)
def register(body: Credentials, db: sqlite3.Connection = Depends(get_db)):
    salt = secrets.token_hex(16)
    try:
        db.execute("INSERT INTO users (email, salt, password_hash) VALUES (?, ?, ?)",
                   (body.email, salt, hash_password(body.password, salt)))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "email already registered")
    return {"email": body.email}


@app.post("/login")
def login(body: Credentials, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT salt, password_hash FROM users WHERE email = ?", (body.email,)).fetchone()
    if row is None or hash_password(body.password, row["salt"]) != row["password_hash"]:
        raise HTTPException(401, "invalid credentials")
    return {"token": secrets.token_urlsafe(32)}
