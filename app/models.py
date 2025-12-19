from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")


class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)  # For UI customization
    icon = Column(String, nullable=True)  # Emoji or icon name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="folders")
    notes = relationship("Note", back_populates="folder", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    title = Column(String, nullable=True)
    
    # OCR data
    raw_text = Column(Text, nullable=True)  # Original OCR output (never modified)
    corrected_text = Column(Text, nullable=True)  # User-edited version
    
    # Legacy field for backward compatibility
    text = Column(Text, nullable=True)  # Maps to corrected_text
    
    # Image storage
    image_path = Column(String, nullable=True)  # Local path (legacy)
    image_url = Column(String, nullable=True)  # Cloud storage URL (new)
    
    # OCR metadata
    line_count = Column(Integer, default=0)
    average_confidence = Column(String, nullable=True)  # Store as string for flexibility
    lines = Column(Text, nullable=True)  # JSON string of lines array
    
    # Timestamps
    timestamp = Column(Integer, nullable=True)  # Unix timestamp from mobile
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Sync metadata
    synced_at = Column(DateTime(timezone=True), nullable=True)  # When last synced to cloud
    
    # Relationships
    user = relationship("User", back_populates="notes")
    folder = relationship("Folder", back_populates="notes")
