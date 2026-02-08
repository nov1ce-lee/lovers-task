from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import Reward, Redemption, User, Transaction
from auth import get_current_user

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.post("/", response_model=Reward)
def create_reward(reward: Reward, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    session.add(reward)
    session.commit()
    session.refresh(reward)
    return reward

@router.get("/", response_model=List[Reward])
def read_rewards(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    rewards = session.exec(select(Reward).where(Reward.is_active == True)).all()
    return rewards

@router.post("/{reward_id}/redeem")
def redeem_reward(reward_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    reward = session.get(Reward, reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if reward.stock == 0:
        raise HTTPException(status_code=400, detail="Out of stock")
    
    if current_user.balance < reward.cost:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct balance
    current_user.balance -= reward.cost
    session.add(current_user)
    
    # Reduce stock if not infinite
    if reward.stock > 0:
        reward.stock -= 1
        session.add(reward)
        
    # Create redemption record
    redemption = Redemption(
        user_id=current_user.id,
        reward_id=reward_id,
        cost_snapshot=reward.cost,
        status="pending"
    )
    session.add(redemption)
    
    # Record transaction
    tx = Transaction(
        user_id=current_user.id,
        amount=-reward.cost,
        type="redemption",
        description=f"Redeemed: {reward.title}"
    )
    session.add(tx)
    
    session.commit()
    return {"message": "Reward redeemed successfully"}

@router.get("/redemptions", response_model=List[Redemption])
def read_redemptions(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Return all redemptions
    redemptions = session.exec(select(Redemption).order_by(Redemption.created_at.desc())).all()
    return redemptions

@router.post("/redemptions/{redemption_id}/fulfill")
def fulfill_redemption(redemption_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    redemption = session.get(Redemption, redemption_id)
    if not redemption:
        raise HTTPException(status_code=404, detail="Redemption not found")
    
    redemption.status = "fulfilled"
    session.add(redemption)
    session.commit()
    return {"message": "Redemption fulfilled"}
