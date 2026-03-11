from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    # Legacy
    BUYER = "buyer"
    MANAGER = "manager"
    
    # New RBAC Roles
    SOURCING_BUYER = "sourcing_buyer"
    QA_MANAGER = "qa_manager"
    PROCUREMENT_MANAGER = "procurement_manager"

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.SOURCING_BUYER

class UserOut(UserBase):
    id: int
    full_name: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class ProjectBase(BaseModel):
    rfq_id: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass


class ExtractedItemBase(BaseModel):
    item_name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    lead_time: Optional[str] = None
    moq: Optional[int] = None
    payment_terms: Optional[str] = None
    iatf_compliance: Optional[str] = None
    material_spec: Optional[str] = None
    part_number: Optional[str] = None

class ExtractedItemCreate(ExtractedItemBase):
    pass

class ExtractedItem(ExtractedItemBase):
    id: int
    bid_id: int

    class Config:
        from_attributes = True

class BidBase(BaseModel):
    vendor_name: Optional[str] = None
    filename: str
    rfq_id: str
    project_id: Optional[int] = None
    rfq_filename: Optional[str] = None
    
    # Extract Fields
    total_cost: Optional[float] = None
    lead_time: Optional[str] = None
    payment_terms: Optional[str] = None
    compliance_status: Optional[str] = None

class BidCreate(BidBase):
    pass

class BidDecision(BaseModel):
    status: str
    comment: Optional[str] = None

class RiskFlag(BaseModel):
    """Structured risk flag with category, severity, and evidence."""
    risk: str
    category: str = "COMPLIANCE"  # CERTIFICATION|PAYMENT|WARRANTY|LEAD_TIME|INCOTERMS|CLAUSE|NUMERIC|COMPLIANCE
    severity: str = "medium"      # critical|high|medium|low
    evidence: str = ""
    source: str = "programmatic"  # programmatic|llm|hybrid

class Bid(BidBase):
    id: int
    status: str
    created_at: Optional[datetime] = None

    # Automotive
    incoterms: Optional[str] = None
    warranty_terms: Optional[str] = None
    is_iatf_certified: bool = False
    risk_flags: Optional[str] = None # JSON string (structured RiskFlag objects)

    score: float = 0.0
    score_breakdown: Optional[dict] = None # Detailed scoring info
    reviewer_comments: Optional[str] = None

    # Compliance summary counts (computed, not stored)
    compliance_summary: Optional[dict] = None  # {"critical": 2, "high": 1, "medium": 0, "low": 1, "total": 4}

    items: List[ExtractedItem] = []

    class Config:
        from_attributes = True

class Project(ProjectBase):
    id: int
    status: str
    rfq_filename: Optional[str] = None
    rfq_raw_text: Optional[str] = None
    rfq_requirements: Optional[str] = None
    created_at: datetime
    bids: List['Bid'] = []

    class Config:
        from_attributes = True

class ScoringWeights(BaseModel):
    price: float = 0.5
    lead_time: float = 0.3
    compliance: float = 0.2

class AnalysisRequest(BaseModel):
    rfq_id: str
    weights: Optional[ScoringWeights] = None

class AuditLog(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

# For forward references
Project.update_forward_refs()
Bid.update_forward_refs()
