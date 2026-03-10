from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Enum as SqEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class UserRole(str, enum.Enum):
    # Legacy
    BUYER = "buyer" 
    MANAGER = "manager"
    
    # New RBAC Roles
    SOURCING_BUYER = "sourcing_buyer"
    QA_MANAGER = "qa_manager"
    PROCUREMENT_MANAGER = "procurement_manager"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(String, unique=True, index=True)
    title = Column(String)
    category = Column(String, nullable=True) # e.g., Machined Parts, Electronics
    description = Column(Text, nullable=True)
    status = Column(String, default="Open")
    rfq_filename = Column(String, nullable=True)
    rfq_raw_text = Column(Text, nullable=True)
    rfq_requirements = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    bids = relationship("Bid", back_populates="project")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String) # e.g., "UPLOAD", "APPROVE", "REJECT", "SCORE_UPDATE"
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(Text, nullable=True) # JSON string of details
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SqEnum(UserRole), default=UserRole.SOURCING_BUYER)
    full_name = Column(String, nullable=True)

class BidStatus(str, enum.Enum):
    PENDING = "pending"
    INGESTED = "ingested"
    EXTRACTION_FAILED = "extraction_failed"
    APPROVED = "approved"
    REJECTED = "rejected"
    HOLD = "hold"
    SHORTLISTED = "shortlisted"

class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    rfq_id = Column(String, index=True) # Redundant but kept for easy filtering
    vendor_name = Column(String, index=True)
    filename = Column(String)
    
    # Extracted Summary Fields
    total_cost = Column(Float, nullable=True)
    lead_time = Column(String, nullable=True)
    payment_terms = Column(String, nullable=True)
    compliance_status = Column(String, nullable=True) # "Yes", "No", "Partial"

    # Raw extracted text (optional, for debugging)
    raw_text = Column(Text)
    
    # Week 6: Scoring & Governance
    status = Column(SqEnum(BidStatus), default=BidStatus.PENDING)
    score = Column(Float, default=0.0)
    reviewer_comments = Column(Text, nullable=True)
    
    # Automotive Specifics
    incoterms = Column(String, nullable=True)
    warranty_terms = Column(String, nullable=True)
    is_iatf_certified = Column(Boolean, default=False)
    risk_flags = Column(Text, nullable=True) # Stored as JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="bids")
    items = relationship("ExtractedItem", back_populates="bid")

class ExtractedItem(Base):
    __tablename__ = "extracted_items"

    id = Column(Integer, primary_key=True, index=True)
    bid_id = Column(Integer, ForeignKey("bids.id"))
    
    item_name = Column(String)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    lead_time = Column(String, nullable=True) # e.g. "4 weeks"
    moq = Column(Integer, nullable=True) # Minimum Order Quantity
    payment_terms = Column(String, nullable=True)
    iatf_compliance = Column(String, nullable=True) # "Yes", "No", "Unknown"
    
    # Technical Specs
    material_spec = Column(String, nullable=True)
    part_number = Column(String, nullable=True)
    
    bid = relationship("Bid", back_populates="items")
