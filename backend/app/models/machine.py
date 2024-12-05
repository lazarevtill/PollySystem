# app/models/machine.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    host = Column(String, unique=True, index=True)
    port = Column(Integer, default=22)
    user = Column(String)
    password = Column(String, nullable=True)
    ssh_key_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
