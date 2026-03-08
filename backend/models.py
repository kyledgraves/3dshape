from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, Boolean, ForeignKey, 
    DateTime, JSON, Numeric, LargeBinary
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    parts = relationship("Part", back_populates="account")
    scenes = relationship("Scene", back_populates="account")


class Part(Base):
    __tablename__ = "parts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    supplied_id = Column(String(255))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    part_metadata = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    account = relationship("Account", back_populates="parts")
    revisions = relationship("PartRevision", back_populates="part", cascade="all, delete-orphan")


class PartRevision(Base):
    __tablename__ = "part_revisions"
    
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id", ondelete="CASCADE"))
    revision_number = Column(Integer, nullable=False)
    supplied_id = Column(String(255))
    status = Column(String(50), default="draft")
    part_metadata = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    part = relationship("Part", back_populates="revisions")
    files = relationship("File", back_populates="part_revision", cascade="all, delete-orphan")
    geometry = relationship("Geometry", back_populates="part_revision", cascade="all, delete-orphan")
    scene_items = relationship("SceneItem", back_populates="part_revision")


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    part_revision_id = Column(Integer, ForeignKey("part_revisions.id", ondelete="CASCADE"))
    original_filename = Column(String(255))
    file_data = Column(LargeBinary)
    file_size = Column(BigInteger)
    status = Column(String(50), default="pending")
    
    part_revision = relationship("PartRevision", back_populates="files")


class Geometry(Base):
    __tablename__ = "geometry"
    
    id = Column(Integer, primary_key=True, index=True)
    part_revision_id = Column(Integer, ForeignKey("part_revisions.id", ondelete="CASCADE"))
    format = Column(String(50))
    version = Column(String(50))
    vertex_count = Column(Integer)
    face_count = Column(Integer)
    bounding_box = Column(JSON)
    data = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    part_revision = relationship("PartRevision", back_populates="geometry")


class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    name = Column(String(255), nullable=False)
    state = Column(String(50), default="draft")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    account = relationship("Account", back_populates="scenes")
    items = relationship("SceneItem", back_populates="scene", cascade="all, delete-orphan")
    render_sessions = relationship("RenderSession", back_populates="scene", cascade="all, delete-orphan")


class SceneItem(Base):
    __tablename__ = "scene_items"
    
    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"))
    part_revision_id = Column(Integer, ForeignKey("part_revisions.id", ondelete="CASCADE"))
    transform_matrix = Column(JSON, default={})
    visibility = Column(Boolean, default=True)
    
    scene = relationship("Scene", back_populates="items")
    part_revision = relationship("PartRevision", back_populates="scene_items")


class RenderSession(Base):
    __tablename__ = "render_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"))
    user_id = Column(Integer)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    scene = relationship("Scene", back_populates="render_sessions")
