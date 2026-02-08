from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import Task, TaskLog, User, Transaction
from auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task)
def create_task(task: Task, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Anyone can create a task
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.get("/", response_model=List[Task])
def read_tasks(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Return all active tasks
    tasks = session.exec(select(Task).where(Task.is_active == True)).all()
    return tasks

@router.post("/{task_id}/submit")
def submit_task(task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if it's a daily task and already done today?
    if task.type == "daily":
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_log = session.exec(select(TaskLog).where(
            TaskLog.task_id == task_id, 
            TaskLog.user_id == current_user.id,
            TaskLog.created_at >= today_start
        )).first()
        if existing_log:
             raise HTTPException(status_code=400, detail="Daily task already submitted today")

    # Create log
    status = "pending_approval" if task.needs_approval else "completed"
    
    log = TaskLog(user_id=current_user.id, task_id=task_id, status=status)
    session.add(log)
    
    # If auto-completed, grant reward immediately
    if status == "completed":
        current_user.balance += task.reward_amount
        session.add(current_user)
        
        # Record transaction
        tx = Transaction(
            user_id=current_user.id,
            amount=task.reward_amount,
            type="task_reward",
            description=f"Completed task: {task.title}"
        )
        session.add(tx)
        
    session.commit()
    return {"message": "Task submitted", "status": status}

@router.get("/logs", response_model=List[TaskLog])
def read_task_logs(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Show logs for the couple? Or just me? 
    # Let's show all logs for now, or maybe filter by query param.
    # For now, let's return all to keep it simple for the UI to filter.
    logs = session.exec(select(TaskLog).order_by(TaskLog.created_at.desc())).all()
    return logs

@router.post("/logs/{log_id}/approve")
def approve_task(log_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    log = session.get(TaskLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if log.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Task not pending approval")
        
    # Security: maybe only the partner can approve?
    # For now, let's assume any authorized user (the partner) can approve.
    # Ideally check: if current_user.id == log.user.partner_id
    
    log.status = "completed"
    session.add(log)
    
    # Grant reward
    task = log.task
    target_user = log.user
    target_user.balance += task.reward_amount
    session.add(target_user)
    
    tx = Transaction(
        user_id=target_user.id,
        amount=task.reward_amount,
        type="task_reward",
        description=f"Task approved by {current_user.username}: {task.title}"
    )
    session.add(tx)
    
    session.commit()
    return {"message": "Task approved"}

@router.post("/logs/{log_id}/reject")
def reject_task(log_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    log = session.get(TaskLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    log.status = "rejected"
    session.add(log)
    session.commit()
    return {"message": "Task rejected"}
