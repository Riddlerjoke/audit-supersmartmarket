

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from backend.database import Base


class Log(Base):
    __tablename__ = "logs"
    log_id = Column(Integer, primary_key=True, index=True)
    id_user = Column(String(50))
    event_time = Column(TIMESTAMP, nullable=False)
    operation = Column(String(10))
    target_table = Column(String(50))
    target_id = Column(String(50))
    field_name = Column(String(100))
    detail = Column(Text, nullable=True)
