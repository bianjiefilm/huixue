"""
Add trainings.designer_type for the public project detail "view training" entry.

Values:
- BI: BI designer
- AI: AI designer
- JUPYTER: Jupyter editor
- NULL: hide the public "查看实训" launch button
"""

import logging
import os

from sqlalchemy import create_engine, text


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./huixue_local.db")


def add_training_designer_type():
    engine = create_engine(DATABASE_URL, echo=True)

    with engine.connect() as conn:
        try:
            logger.info("Adding trainings.designer_type")
            conn.execute(text("ALTER TABLE trainings ADD COLUMN designer_type VARCHAR(20) DEFAULT NULL"))
            conn.commit()
            logger.info("Added trainings.designer_type")
        except Exception as exc:
            message = str(exc).lower()
            if "duplicate column" in message or "already exists" in message:
                logger.info("trainings.designer_type already exists, skipping")
                conn.rollback()
                return
            conn.rollback()
            raise


def main():
    logger.info("Starting trainings.designer_type migration")
    add_training_designer_type()
    logger.info("Migration complete")


if __name__ == "__main__":
    main()
