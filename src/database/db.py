import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("DatabaseManager")


class DatabaseManager:
    """Lightweight wrapper around SQLAlchemy to persist validation results."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL is not configured")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            future=True,
        )
        self.metadata = MetaData()

        self.validation_results = Table(
            "validation_results",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("request_id", String(255), unique=True, nullable=False),
            Column(
                "timestamp",
                DateTime(timezone=True),
                server_default=text("CURRENT_TIMESTAMP"),
            ),
            Column("input_types", JSON),
            Column("image_valid", Boolean),
            Column("text_valid", Boolean),
            Column("voice_valid", Boolean),
            Column("overall_confidence", Float),
            Column("routing", String(50)),
            Column("action", String(50)),
            Column("raw_results", JSON),
        )

        self.feedback_logs = Table(
            "feedback_logs",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("request_id", String(255)),
            Column("modality", String(50)),
            Column("predicted_label", String(255)),
            Column("user_correction", String(255)),
            Column("is_correct", Boolean),
            Column("comments", String),
            Column(
                "timestamp",
                DateTime(timezone=True),
                server_default=text("CURRENT_TIMESTAMP"),
            ),
        )

        self.metadata.create_all(self.engine)
        logger.info("Database tables ensured.")

    def save_validation_result(self, request_id: str, payload: Dict[str, Any]) -> None:
        """Persist full validation payload; failures are logged but non-blocking."""
        record = {
            "request_id": request_id,
            "timestamp": datetime.now(),
            "input_types": payload.get("input_types"),
            "image_valid": payload.get("image", {}).get("valid") if payload.get("image") else None,
            "text_valid": payload.get("text", {}).get("valid") if payload.get("text") else None,
            "voice_valid": payload.get("voice", {}).get("valid") if payload.get("voice") else None,
            "overall_confidence": payload.get("confidence", {}).get("overall_confidence"),
            "routing": payload.get("confidence", {}).get("routing"),
            "action": payload.get("confidence", {}).get("action"),
            "raw_results": payload,
        }

        try:
            with self.engine.begin() as connection:
                connection.execute(self.validation_results.insert().values(**record))
        except SQLAlchemyError as exc:
            logger.warning("Failed to persist validation result: %s", exc)

