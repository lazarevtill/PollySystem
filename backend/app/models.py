from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    ssh_port = Column(Integer, nullable=False, default=22)
    ssh_user = Column(String(255), nullable=False)
    ssh_key_private = Column(Text, nullable=False)
    ssh_key_public = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deployments = relationship("Deployment", back_populates="machine", cascade="all, delete-orphan")

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    deployment_type = Column(String(50), nullable=False)  # 'container' or 'compose'
    config = Column(Text, nullable=False)  # JSON string
    subdomain = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), nullable=False)  # running, stopped, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    machine = relationship("Machine", back_populates="deployments")
