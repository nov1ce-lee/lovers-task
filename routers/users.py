from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import User
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    statement = select(User).where(User.username == user.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # No password hash needed
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[User])
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.post("/bind_partner/{partner_id}")
def bind_partner(partner_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if partner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot bind yourself as partner")
    
    partner = session.get(User, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    current_user.partner_id = partner_id
    partner.partner_id = current_user.id
    
    session.add(current_user)
    session.add(partner)
    session.commit()
    return {"message": f"Successfully bound with {partner.username}"}
