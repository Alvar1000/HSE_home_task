from datetime import datetime

from sqlalchemy import Integer, Column, String, DateTime, Boolean, TIMESTAMP, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Link(Base):
    __tablename__ = 'link'

    id = Column(Integer, primary_key = True, index = True)
    original_url = Column(String, nullable = False)
    short_code = Column(String, unique = True, index = True)
    custom_alias = Column(String, unique=True, nullable=True)
    create_at = Column(Date, default=datetime.utcnow().date())
    expires_at = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)
    last_accessed_at = Column(Date, nullable=True)