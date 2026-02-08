from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    # password_hash removed
    balance: float = Field(default=0.0)
    
    task_logs: List["TaskLog"] = Relationship(back_populates="user")
    redemptions: List["Redemption"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    
    # We can store the partner ID explicitly or just assume 2 users system
    partner_id: Optional[int] = Field(default=None)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    reward_amount: float
    type: str = Field(default="one_time") # daily, one_time
    penalty_amount: float = Field(default=0.0)
    needs_approval: bool = Field(default=False)
    is_active: bool = Field(default=True)
    
    task_logs: List["TaskLog"] = Relationship(back_populates="task")

class TaskLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    task_id: int = Field(foreign_key="task.id")
    status: str = Field(default="completed") # pending, completed, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="task_logs")
    task: Task = Relationship(back_populates="task_logs")

class Reward(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    cost: float
    stock: int = Field(default=-1)
    is_active: bool = Field(default=True)
    
    redemptions: List["Redemption"] = Relationship(back_populates="reward")

class Redemption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    reward_id: int = Field(foreign_key="reward.id")
    cost_snapshot: float
    status: str = Field(default="pending") # pending, fulfilled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="redemptions")
    reward: Reward = Relationship(back_populates="redemptions")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float
    type: str # task_reward, redemption, penalty, manual
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="transactions")
