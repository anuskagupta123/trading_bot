from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..database.database import get_db
from ..database.models import Broker

router = APIRouter(prefix="/brokers", tags=["brokers"])

# Pydantic models for request/response
class BrokerConnect(BaseModel):
    user_id: int
    broker_name: str  # "zerodha" or "shoonya"
    api_key: str
    api_secret: str

class BrokerResponse(BaseModel):
    id: int
    user_id: int
    broker_name: str
    api_key: str
    access_token: str = None
    is_active: bool
    
    class Config:
        from_attributes = True

class BrokerUpdate(BaseModel):
    access_token: str
    is_active: bool = True

@router.post("/connect", response_model=dict)
def connect_broker(
    broker_data: BrokerConnect,
    db: Session = Depends(get_db)
):
    """
    Connect a broker account. User needs to get access_token separately.
    """
    # Check if broker already exists for this user
    existing = db.query(Broker).filter(
        Broker.user_id == broker_data.user_id,
        Broker.broker_name == broker_data.broker_name
    ).first()
    
    if existing:
        # Update existing broker
        existing.api_key = broker_data.api_key
        existing.api_secret = broker_data.api_secret
    else:
        # Create new broker entry
        broker = Broker(
            user_id=broker_data.user_id,
            broker_name=broker_data.broker_name,
            api_key=broker_data.api_key,
            api_secret=broker_data.api_secret
        )
        db.add(broker)
    
    db.commit()
    return {
        "message": "Broker credentials saved. Complete OAuth login to get access token.",
        "broker_name": broker_data.broker_name,
        "next_step": f"Redirect user to {broker_data.broker_name} login page"
    }

@router.get("/status/{user_id}", response_model=List[BrokerResponse])
def broker_status(user_id: int, db: Session = Depends(get_db)):
    """
    Get all connected brokers for a user.
    """
    brokers = db.query(Broker).filter(Broker.user_id == user_id).all()
    return brokers

@router.get("/{broker_id}", response_model=BrokerResponse)
def get_broker(broker_id: int, db: Session = Depends(get_db)):
    """
    Get a specific broker's details.
    """
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    return broker

@router.put("/{broker_id}", response_model=BrokerResponse)
def update_broker(
    broker_id: int,
    broker_update: BrokerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update broker with access token (after OAuth login).
    """
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    broker.access_token = broker_update.access_token
    broker.is_active = broker_update.is_active
    db.commit()
    db.refresh(broker)
    return broker

@router.delete("/{broker_id}", response_model=dict)
def disconnect_broker(broker_id: int, db: Session = Depends(get_db)):
    """
    Disconnect a broker (soft delete).
    """
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    broker.is_active = False
    db.commit()
    return {"message": "Broker disconnected"}
