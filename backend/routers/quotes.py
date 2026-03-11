from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from database import get_db
import models, schemas
from services import docling_extractor, llm_extractor, scoring, compliance_engine
from dependencies import get_current_user, RoleChecker
from models import UserRole
import shutil
import os
import uuid

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"]
)

# Project Management
@router.post("/projects", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate, 
    db: Session = Depends(get_db),
    _: models.User = Depends(RoleChecker([UserRole.SOURCING_BUYER, UserRole.PROCUREMENT_MANAGER]))
):
    try:
        print(f"DEBUG: Creating project with rfq_id: {project.rfq_id}")
        db_project = models.Project(**project.dict())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception as e:
        db.rollback()
        print(f"ERROR creating project: {str(e)}")
        # Check if it's a uniqueness error
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="The RFQ ID already exists. Please use a unique ID.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/projects", response_model=List[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.get("/projects/{rfq_id}", response_model=schemas.Project)
def get_project(rfq_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/projects/{rfq_id}")
def delete_project(
    rfq_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.PROCUREMENT_MANAGER]))
):
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Cascade delete bids and items handled by relationship or manual
    bids = db.query(models.Bid).filter(models.Bid.rfq_id == rfq_id).all()
    for bid in bids:
        db.query(models.ExtractedItem).filter(models.ExtractedItem.bid_id == bid.id).delete()
        db.delete(bid)
    
    db.delete(project)
    
    # Audit Log
    log = models.AuditLog(
        action="PROJECT_DELETE",
        user_id=current_user.id,
        details=f"Deleted project {rfq_id}"
    )
    db.add(log)
    db.commit()
    return {"message": "Project deleted successfully"}

@router.post("/upload-rfq", response_model=schemas.Project)
async def upload_rfq(
    rfq_id: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.SOURCING_BUYER, UserRole.PROCUREMENT_MANAGER]))
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save upload file temporarily
    temp_filename = f"temp_rfq_{uuid.uuid4()}.pdf"
    await file.seek(0)
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 1. Update Project record immediately (Ingest)
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    if not project:
        if os.path.exists(temp_filename): os.remove(temp_filename)
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.status = "Ingesting..."
    db.commit()

    text = None
    try:
        # 2. Extract Content
        text = docling_extractor.extract_content_from_doc(temp_filename)
    except Exception as e:
        print(f"ERROR: Extraction failed during upload: {str(e)}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    # 3. Update Result
    project.rfq_filename = file.filename
    project.rfq_raw_text = text
    if not text:
        project.status = "Extraction Failed"
    else:
        project.status = "Ingested"
        # Optional: Reset requirements to ensure they are re-extracted on next analysis
        project.rfq_requirements = None

    
    # Audit Log
    log = models.AuditLog(
        action="RFQ_UPLOAD",
        user_id=current_user.id,
        details=f"Uploaded Master RFQ for project {rfq_id}"
    )
    db.add(log)
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/projects/{rfq_id}/rfq")
def delete_rfq(
    rfq_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.PROCUREMENT_MANAGER]))
):
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.rfq_raw_text = None
    project.rfq_requirements = None
    project.status = "Open"
    
    # Audit Log
    log = models.AuditLog(
        action="RFQ_DELETE",
        user_id=current_user.id,
        details=f"Deleted Master RFQ for project {rfq_id}"
    )
    db.add(log)
    db.commit()
    return {"message": "Master RFQ removed successfully"}

@router.post("/upload", response_model=schemas.Bid)
async def upload_bid(
    rfq_id: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.SOURCING_BUYER, UserRole.PROCUREMENT_MANAGER]))
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save upload file temporarily
    temp_filename = f"temp_bid_{uuid.uuid4()}.pdf"
    await file.seek(0)
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    text = None
    try:
        # 1. Extract Content
        text = docling_extractor.extract_content_from_doc(temp_filename)
    except Exception as e:
        print(f"Extraction failed for bid {file.filename}: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    # 2. JUST Save to DB (LLM moved to process-analysis)
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    project_id = project.id if project else None
    
    bid_status = models.BidStatus.INGESTED if text else models.BidStatus.EXTRACTION_FAILED
    
    db_bid = models.Bid(
        project_id=project_id,
        rfq_id=rfq_id,
        vendor_name="Processing Pending..." if text else "Extraction Failed (Click to Remove)",
        filename=file.filename,
        raw_text=text,
        total_cost=0.0,
        status=bid_status
    )
    db.add(db_bid)
    
    # Audit Log
    log = models.AuditLog(
        action="BID_UPLOAD",
        user_id=current_user.id,
        details=f"Uploaded vendor bid for RFQ {rfq_id} - Filename: {file.filename}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_bid)
    return db_bid

def _compute_compliance_summary(risk_flags_json: str) -> dict:
    """Computes severity counts from structured risk flags JSON."""
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
    if not risk_flags_json:
        return summary
    try:
        flags = json.loads(risk_flags_json)
        if not isinstance(flags, list):
            return summary
        for flag in flags:
            severity = flag.get("severity", "medium") if isinstance(flag, dict) else "medium"
            if severity in summary:
                summary[severity] += 1
            summary["total"] += 1
    except Exception:
        pass
    return summary


@router.get("/compare-bids/{rfq_id}", response_model=List[schemas.Bid])
def compare_bids(rfq_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all bids associated with a specific RFQ ID, enriched with compliance summaries.
    """
    bids = db.query(models.Bid).filter(models.Bid.rfq_id == rfq_id).all()
    # Enrich with compliance_summary
    result = []
    for bid in bids:
        if hasattr(schemas.Bid, "from_orm"):
            bid_dto = schemas.Bid.from_orm(bid)
        else:
            bid_dto = schemas.Bid.model_validate(bid)
        bid_dto.compliance_summary = _compute_compliance_summary(bid.risk_flags)
        result.append(bid_dto)
    return result

@router.post("/score", response_model=List[schemas.Bid])
def calculate_scores(request: schemas.AnalysisRequest, db: Session = Depends(get_db)):
    """
    Calculates scores for all bids of an RFQ based on weights.
    Returns the updated bids.
    """
    bids = db.query(models.Bid).filter(models.Bid.rfq_id == request.rfq_id).all()
    if not bids:
        return []
    
    # Convert ORM to dict for scoring service
    bids_data = []
    # Helper for quick normalization if needed (should be in DB ideally)
    from services import normalization
    
    for bid in bids:
        # Helper for handling cost
        try:
            cost = float(bid.total_cost) if bid.total_cost is not None else 0.0
        except ValueError:
            cost = 0.0
            
        # Update DB object instantly to fix bad data (Validation Error prevention)
        if bid.total_cost != cost:
            bid.total_cost = cost

        bid_dict = {
            "id": bid.id,
            "total_cost": cost,
            "lead_time": bid.lead_time,
            "compliance_status": bid.compliance_status,
            "is_iatf_certified": bid.is_iatf_certified,
            # Ensure we have days for calculation
            "lead_time_days": normalization.normalize_lead_time(bid.lead_time) if bid.lead_time else 0
        }
        bids_data.append(bid_dict)

    weights_dict = request.weights.dict() if request.weights else {"price": 0.5, "lead_time": 0.3, "compliance": 0.2}
    
    # Calculate scores with breakdowns
    try:
        scored_data = scoring.score_bids(bids_data, weights_dict)
    except Exception as e:
        print(f"Scoring Error: {e}")
        return [] # Return empty or handle gracefully
    
    # Update DB with just the scalar score (breakdown is transient for now or needs JSON column)
    # The frontend calculates breakdown on the fly? No, the backend should return it.
    # We can return the scored_data directly since it already matches the schema largely, 
    # but we need to merge it with the ORM objects if we want to return full Bid objects.
    # Better approach: Update the score in DB, and return the `scored_data` list which has everything we need for the table.
    # Actually, schema `Bid` needs to be updated to include `score_breakdown` (optional) if we want to return it typed.
    # For now, let's just update the score in DB and return the logic-enriched dicts.
    
    # Update DB and prepare response
    final_response = []
    
    for s_bid in scored_data:
        db_bid = next((b for b in bids if b.id == s_bid["id"]), None)
        if db_bid:
            # Update Score in DB
            db_bid.score = s_bid["score"]
            
            # Create full response object from DB model
            # Prioritize from_orm because schema uses V1 config (orm_mode=True)
            if hasattr(schemas.Bid, "from_orm"):
                bid_dto = schemas.Bid.from_orm(db_bid)
            else:
                bid_dto = schemas.Bid.model_validate(db_bid)
                
            # Inject the breakdown and compliance summary
            bid_dto.score_breakdown = s_bid.get("score_breakdown")
            bid_dto.compliance_summary = _compute_compliance_summary(db_bid.risk_flags)
            final_response.append(bid_dto)
    
    db.commit()
    
    return final_response

@router.patch("/bids/{bid_id}/status")
def update_bid_status(
    bid_id: int, 
    decision: schemas.BidDecision,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.PROCUREMENT_MANAGER]))
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    old_status = bid.status
    bid.status = decision.status
    
    # Save reviewer comment if provided
    if decision.comment is not None:
        bid.reviewer_comments = decision.comment
    
    # Audit Log
    comment_text = f" | Comment: {decision.comment}" if decision.comment else ""
    log = models.AuditLog(
        action=f"STATUS_UPDATE_{decision.status.upper()}",
        user_id=current_user.id,
        details=f"Changed bid {bid_id} ({bid.vendor_name}) from {old_status} to {decision.status}{comment_text}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(bid)
    return bid

@router.patch("/bids/{bid_id}/comment")
def update_bid_comment(
    bid_id: int, 
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.PROCUREMENT_MANAGER]))
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bid.reviewer_comments = payload.get("comment", "")
    
    # Audit Log
    log = models.AuditLog(
        action="REVIEWER_COMMENT",
        user_id=current_user.id,
        details=f"Comment on bid {bid_id} ({bid.vendor_name}): {bid.reviewer_comments}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(bid)
    return bid

@router.delete("/bids/{bid_id}")
def delete_bid(
    bid_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker([UserRole.PROCUREMENT_MANAGER]))
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Delete extracted items first
    db.query(models.ExtractedItem).filter(models.ExtractedItem.bid_id == bid_id).delete()
    
    db.delete(bid)
    
    # Audit Log
    log = models.AuditLog(
        action="BID_DELETE",
        user_id=current_user.id,
        details=f"Deleted bid {bid_id} - Vendor: {bid.vendor_name}"
    )
    db.add(log)
    
    db.commit()
    return {"message": "Bid deleted successfully"}

@router.post("/analyze")
async def analyze_rfq(request: schemas.AnalysisRequest, db: Session = Depends(get_db)):
    """
    Generates an Executive Summary for the RFQ.
    """
    project = db.query(models.Project).filter(models.Project.rfq_id == request.rfq_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    bids = db.query(models.Bid).filter(models.Bid.rfq_id == request.rfq_id).all()
    
    # 3. Prepare data for LLM (including scores)
    # Convert ORM to dict
    bids_data = []
    from services import normalization, scoring # Ensure imports
    
    for bid in bids:
        bid_dict = {
            "id": bid.id,
            "vendor_name": bid.vendor_name,
            "total_cost": bid.total_cost,
            "lead_time": bid.lead_time,
            "compliance_status": bid.compliance_status,
            "is_iatf_certified": bid.is_iatf_certified,
            "lead_time_days": normalization.normalize_lead_time(bid.lead_time) if bid.lead_time else 0
        }
        bids_data.append(bid_dict)

    # Calculate scores with default weights for the analysis context
    # (User might have custom weights in UI, but for initial analysis we use defaults)
    default_weights = {"price": 0.5, "lead_time": 0.3, "compliance": 0.2}
    scored_bids = scoring.score_bids(bids_data, default_weights)
    
    rfq_text = project.rfq_raw_text or ""
    rfq_requirements = project.rfq_requirements
    
    # Generate Summary with Score Context
    summary = llm_extractor.generate_executive_summary(scored_bids, rfq_requirements)

    return {"summary": summary}

@router.post("/process-analysis/{rfq_id}")
async def process_analysis(
    rfq_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Triggers extraction and analysis for all unprocessed docs in a project.
    """
    project = db.query(models.Project).filter(models.Project.rfq_id == rfq_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 1. Ensure RFQ requirements are extracted
    if not project.rfq_requirements or project.rfq_requirements == "{}":
        if project.rfq_raw_text:
            requirements = llm_extractor.extract_rfq_requirements(project.rfq_raw_text)
            project.rfq_requirements = json.dumps(requirements)
            db.commit()

    # 2. Process all Bids
    bids = db.query(models.Bid).filter(models.Bid.rfq_id == rfq_id).all()
    
    for bid in bids:
        # ALWAYS re-process if triggered, to ensure "proper results"
        print(f"Processing bid: {bid.filename}")
        
        text = bid.raw_text
        if not text:
            continue
            
        data = llm_extractor.extract_data_from_text(text)
        
        # Update bid
        bid.vendor_name = data.get("VendorName") or data.get("vendor_name") or "Unknown"
        
        raw_cost = data.get("TotalCost") or data.get("total_cost")
        try:
             # Handle strings with $ or ,
             if isinstance(raw_cost, str):
                 bid.total_cost = float(raw_cost.replace("$", "").replace(",", "").strip())
             else:
                 bid.total_cost = float(raw_cost) if raw_cost is not None else 0.0
        except:
             bid.total_cost = 0.0

        bid.lead_time = data.get("LeadTime") or data.get("lead_time") or "N/A"
        bid.payment_terms = data.get("PaymentTerms") or data.get("payment_terms") or "N/A"
        bid.compliance_status = data.get("ComplianceStatus") or data.get("compliance_status") or "Unknown"
        bid.incoterms = data.get("Incoterms") or data.get("incoterms") or "N/A"
        bid.warranty_terms = data.get("Warranty") or data.get("warranty") or "N/A"
        bid.is_iatf_certified = data.get("IATFCertified") or data.get("iatf_certified") or False
        
        # --- Compliance Engine: Build comprehensive, structured risk flags ---
        # Collect raw LLM risk flags
        llm_risk_flags = data.get("risk_flags", [])
        if not isinstance(llm_risk_flags, list):
            llm_risk_flags = []
        # Normalize LLM flags (handle strings)
        normalized_llm_flags = []
        for flag in llm_risk_flags:
            if isinstance(flag, dict) and "risk" in flag:
                normalized_llm_flags.append(flag)
            elif isinstance(flag, str):
                normalized_llm_flags.append({"risk": flag, "evidence": "Identified during AI analysis"})

        # Build bid_data dict for compliance engine
        bid_compliance_data = {
            "vendor_name": bid.vendor_name,
            "total_cost": bid.total_cost,
            "lead_time": bid.lead_time,
            "payment_terms": bid.payment_terms,
            "compliance_status": bid.compliance_status,
            "incoterms": bid.incoterms,
            "warranty_terms": bid.warranty_terms,
            "is_iatf_certified": bid.is_iatf_certified,
        }

        # Parse RFQ requirements
        rfq_reqs = {}
        if project.rfq_requirements and project.rfq_requirements != "{}":
            try:
                rfq_reqs = json.loads(project.rfq_requirements)
            except Exception as e:
                print(f"Error parsing RFQ requirements: {e}")

        # Run the full compliance engine
        structured_flags = compliance_engine.build_compliance_report(
            bid_data=bid_compliance_data,
            rfq_requirements=rfq_reqs,
            llm_risk_flags=normalized_llm_flags,
            bid_raw_text=bid.raw_text or "",
        )

        bid.risk_flags = json.dumps(structured_flags)
        
        # Save items
        db.query(models.ExtractedItem).filter(models.ExtractedItem.bid_id == bid.id).delete()
        for item in data.get("items", []):
            price = item.get("price")
            if isinstance(price, str):
                try:
                    price = float(price.replace("$", "").replace(",", ""))
                except:
                    price = 0.0
            
            new_item = models.ExtractedItem(
                bid_id=bid.id,
                part_number=item.get("part_number"),
                item_name=item.get("item_name") or "Item",
                price=price,
                material_spec=item.get("material_spec"),
                # Carry over payment/compliance from parent if missing in item
                payment_terms=bid.payment_terms,
                iatf_compliance=bid.compliance_status
            )
            db.add(new_item)
    
    db.commit()
    project.status = "Analyzed"
    db.commit()
    
    return {"status": "success", "message": f"Processed {len(bids)} bids for project {rfq_id}"}
