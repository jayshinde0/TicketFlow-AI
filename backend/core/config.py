"""
core/config.py — All application settings loaded from environment variables.
Uses pydantic-settings BaseSettings for automatic env variable binding.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, List
import os


class Settings(BaseSettings):
    # ─── Application ───────────────────────────────────────────────────
    APP_NAME: str = "TicketFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ─── MongoDB ───────────────────────────────────────────────────────
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017", env="MONGODB_URL"
    )
    DATABASE_NAME: str = "ticketflow_ai"

    # ─── JWT Authentication ────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="ticketflow-super-secret-change-in-production",
        env="JWT_SECRET_KEY"
    )
    # Alias used by security.py
    SECRET_KEY: str = Field(
        default="ticketflow-super-secret-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Redis ────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379", env="REDIS_URL"
    )
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")

    # ─── Ollama / LLM ─────────────────────────────────────────────────
    OLLAMA_URL: str = Field(
        default="http://localhost:11434", env="OLLAMA_URL"
    )
    OLLAMA_MODEL: str = Field(default="mistral-nemo", env="OLLAMA_MODEL")
    OLLAMA_TEMPERATURE: float = 0.3
    OLLAMA_MAX_TOKENS: int = 250

    # ─── ChromaDB ─────────────────────────────────────────────────────
    CHROMA_HOST: str = Field(default="localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(default=8001, env="CHROMA_PORT")
    CHROMA_TICKETS_COLLECTION: str = "resolved_tickets"
    CHROMA_ARTICLES_COLLECTION: str = "knowledge_articles"

    # ─── ML / AI Thresholds ───────────────────────────────────────────
    CONFIDENCE_HIGH_THRESHOLD: float = 0.85   # >= this → AUTO_RESOLVE
    CONFIDENCE_LOW_THRESHOLD: float = 0.60    # >= this → SUGGEST_TO_AGENT
    SLA_BREACH_THRESHOLD: float = 0.75        # SLA override trigger
    HALLUCINATION_SIM_THRESHOLD: float = 0.55 # min cosine sim for LLM response
    FEEDBACK_RETRAIN_THRESHOLD: int = 200     # feedback count before retraining
    DUPLICATE_EXACT_THRESHOLD: float = 0.95   # cosine sim for exact duplicate
    DUPLICATE_POSSIBLE_THRESHOLD: float = 0.85 # cosine sim for possible duplicate

    # ─── Sentence Transformer ─────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ─── Sentiment ────────────────────────────────────────────────────
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment"
    SENTIMENT_NEGATIVE_THRESHOLD: float = 0.85  # trigger priority boost

    # ─── Root Cause Detection Thresholds (tickets per time window) ────
    ROOT_CAUSE_THRESHOLDS: Dict[str, Dict] = {
        "Network":        {"count": 8,  "window_minutes": 20},
        "Auth":           {"count": 10, "window_minutes": 15},
        "Software":       {"count": 5,  "window_minutes": 30},
        "Security":       {"count": 3,  "window_minutes": 10},  # P0
        "Database":       {"count": 5,  "window_minutes": 15},
        "Email":          {"count": 8,  "window_minutes": 20},
        "Hardware":       {"count": 6,  "window_minutes": 60},
        "Access":         {"count": 7,  "window_minutes": 20},
        "Billing":        {"count": 6,  "window_minutes": 30},
        "ServiceRequest": {"count": 10, "window_minutes": 30},
    }

    # ─── SLA Limits (minutes) per domain × priority ───────────────────
    SLA_LIMITS: Dict[str, Dict[str, int]] = {
        "Network": {
            "Low": 2880, "Medium": 480, "High": 120, "Critical": 30
        },
        "Auth": {
            "Low": 1440, "Medium": 240, "High": 60, "Critical": 15
        },
        "Software": {
            "Low": 4320, "Medium": 1440, "High": 240, "Critical": 60
        },
        "Hardware": {
            "Low": 4320, "Medium": 1440, "High": 240, "Critical": 120
        },
        "Access": {
            "Low": 2880, "Medium": 480, "High": 120, "Critical": 30
        },
        "Billing": {
            "Low": 2880, "Medium": 1440, "High": 240, "Critical": 60
        },
        "Email": {
            "Low": 2880, "Medium": 480, "High": 120, "Critical": 60
        },
        "Security": {
            "Low": 30, "Medium": 30, "High": 30, "Critical": 5
        },
        "ServiceRequest": {
            "Low": 2880, "Medium": 480, "High": 120, "Critical": 30
        },
        "Database": {
            "Low": 1440, "Medium": 240, "High": 60, "Critical": 5
        },
    }

    # ─── Domain keywords for confidence boost ─────────────────────────
    DOMAIN_KEYWORDS: Dict[str, list] = {
        "Network": [
            "vpn", "wifi", "internet", "dns", "ping", "connection",
            "timeout", "firewall", "network", "router", "packet", "latency"
        ],
        "Auth": [
            "password", "login", "locked", "otp", "2fa", "sso",
            "credentials", "token", "authentication", "unauthorized", "session"
        ],
        "Software": [
            "crash", "error", "install", "update", "freeze", "exception",
            "license", "bug", "software", "application", "app", "broken"
        ],
        "Hardware": [
            "laptop", "screen", "keyboard", "printer", "battery",
            "usb", "monitor", "hardware", "device", "port", "cable"
        ],
        "Access": [
            "access", "permission", "grant", "revoke", "role", "admin",
            "restricted", "denied", "rights", "privileged", "folder"
        ],
        "Billing": [
            "invoice", "payment", "charge", "refund", "subscription",
            "transaction", "billing", "invoice", "credit", "debit", "fee"
        ],
        "Email": [
            "email", "inbox", "attachment", "spam", "mailbox",
            "calendar", "smtp", "outlook", "gmail", "mail", "message"
        ],
        "Security": [
            "phishing", "malware", "virus", "ransomware", "breach",
            "unauthorized", "hack", "attack", "suspicious", "threat"
        ],
        "ServiceRequest": [
            "request", "new", "setup", "provision", "create",
            "onboarding", "license", "order", "need", "want", "please"
        ],
        "Database": [
            "database", "sql", "query", "server", "cpu", "memory",
            "disk", "backup", "db", "mongo", "postgres", "mysql"
        ],
    }

    # ─── Auto-resolve targets per domain ─────────────────────────────
    AUTO_RESOLVE_TARGETS: Dict[str, float] = {
        "Network": 0.35,
        "Auth": 0.65,
        "Software": 0.45,
        "Hardware": 0.25,
        "Access": 0.40,
        "Billing": 0.50,
        "Email": 0.45,
        "Security": 0.05,  # almost never auto-resolve
        "ServiceRequest": 0.55,
        "Database": 0.20,
    }

    # ─── Ticket ID prefix ─────────────────────────────────────────────
    TICKET_ID_PREFIX: str = "TKT"

    # ─── HITL Enhancement settings (Phase 1+) ────────────────────────
    # Higher threshold for sensitive categories
    BILLING_AUTO_RESOLVE_THRESHOLD: float = 0.92
    SECURITY_AUTO_RESOLVE_THRESHOLD: float = 1.0  # effectively never auto-resolve

    # Concurrency limits for the AI pipeline
    MAX_CONCURRENT_PIPELINES: int = 20

    # Department taxonomy
    DEPARTMENT_TAXONOMY: List[str] = [
        "NETWORK", "SOFTWARE", "DATABASE",
        "SECURITY", "BILLING", "HR_FACILITIES",
    ]

    # Category → Department mapping
    CATEGORY_TO_DEPARTMENT: Dict[str, str] = {
        "Network": "NETWORK",
        "Auth": "SOFTWARE",
        "Software": "SOFTWARE",
        "Hardware": "HR_FACILITIES",
        "Access": "SOFTWARE",
        "Billing": "BILLING",
        "Email": "NETWORK",
        "Security": "SECURITY",
        "ServiceRequest": "HR_FACILITIES",
        "Database": "DATABASE",
    }

    # Escalation chain timeouts (minutes)
    ESCALATION_L2_TIMEOUT_MINUTES: int = 15
    ESCALATION_L3_TIMEOUT_MINUTES: int = 30

    # ─── Image upload settings ────────────────────────────────────────
    MAX_IMAGE_SIZE_MB: int = 5
    MAX_IMAGES_PER_TICKET: int = 3
    UPLOAD_DIR: str = "uploads/tickets"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields from env without causing validation errors
        extra = "ignore"


# Singleton settings instance — import this everywhere
settings = Settings()
