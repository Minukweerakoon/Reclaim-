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

        # Novel Feature #1: Spatial-Temporal Learned Patterns Storage
        self.spatial_temporal_patterns = Table(
            "spatial_temporal_patterns",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("item_type", String(100), nullable=False),
            Column("location", String(100), nullable=False),
            Column("time_period", String(50)),  # Can be NULL
            Column("observation_count", Integer, default=1),
            Column(
                "created_at",
                DateTime(timezone=True),
                server_default=text("CURRENT_TIMESTAMP"),
            ),
            Column(
                "updated_at",
                DateTime(timezone=True),
                server_default=text("CURRENT_TIMESTAMP"),
                onupdate=datetime.now,
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

    def save_spatial_temporal_pattern(
        self, item_type: str, location: str, time_period: Optional[str] = None
    ) -> None:
        """
        Save or update a spatial-temporal observation.
        Increments observation_count if the pattern already exists.
        """
        try:
            with self.engine.begin() as connection:
                # Check if pattern exists
                result = connection.execute(
                    self.spatial_temporal_patterns.select().where(
                        (self.spatial_temporal_patterns.c.item_type == item_type)
                        & (self.spatial_temporal_patterns.c.location == location)
                        & (
                            (self.spatial_temporal_patterns.c.time_period == time_period)
                            if time_period
                            else (self.spatial_temporal_patterns.c.time_period.is_(None))
                        )
                    )
                ).first()

                if result:
                    # Update existing pattern
                    connection.execute(
                        self.spatial_temporal_patterns.update()
                        .where(self.spatial_temporal_patterns.c.id == result.id)
                        .values(
                            observation_count=result.observation_count + 1,
                            updated_at=datetime.now(),
                        )
                    )
                    logger.debug(
                        f"Updated pattern: {item_type} @ {location} ({time_period}) - count: {result.observation_count + 1}"
                    )
                else:
                    # Insert new pattern
                    connection.execute(
                        self.spatial_temporal_patterns.insert().values(
                            item_type=item_type,
                            location=location,
                            time_period=time_period,
                            observation_count=1,
                        )
                    )
                    logger.debug(f"New pattern: {item_type} @ {location} ({time_period})")

        except SQLAlchemyError as exc:
            logger.warning(f"Failed to persist spatial-temporal pattern: {exc}")

    def load_spatial_temporal_patterns(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Load all learned patterns from database.
        Returns dict with structure:
        {
            "location": {item1: {loc1: count, loc2: count}, ...},
            "time": {item1: {time1: count, time2: count}, ...}
        }
        """
        patterns = {"location": {}, "time": {}}

        try:
            with self.engine.begin() as connection:
                results = connection.execute(
                    self.spatial_temporal_patterns.select()
                ).fetchall()

                for row in results:
                    item = row.item_type
                    loc = row.location
                    time_p = row.time_period
                    count = row.observation_count

                    # Build location patterns
                    if item not in patterns["location"]:
                        patterns["location"][item] = {}
                    patterns["location"][item][loc] = patterns["location"][item].get(loc, 0) + count

                    # Build time patterns (only if time is specified)
                    if time_p:
                        if item not in patterns["time"]:
                            patterns["time"][item] = {}
                        patterns["time"][item][time_p] = patterns["time"][item].get(time_p, 0) + count

                logger.info(
                    f"Loaded {len(results)} patterns from database "
                    f"({len(patterns['location'])} items, {sum(len(v) for v in patterns['location'].values())} location combos)"
                )

        except SQLAlchemyError as exc:
            logger.warning(f"Failed to load spatial-temporal patterns: {exc}")

        return patterns

