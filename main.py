from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import User
from auth import create_access_token
from routers import users, tasks, rewards
from datetime import timedelta
import auth

app = FastAPI(title="LoveTask API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(rewards.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Seed users
    with Session(auth.get_session().__next__()) as session: # Hacky way to get session, better to use engine directly or just one-off
        # Actually, let's just do it cleanly inside startup
        from database import engine
        with Session(engine) as session:
            for name in ["boy", "girl"]:
                user = session.exec(select(User).where(User.username == name)).first()
                if not user:
                    user = User(username=name)
                    session.add(user)
                    session.commit()
            
            # Bind them if both exist
            boy = session.exec(select(User).where(User.username == "boy")).first()
            girl = session.exec(select(User).where(User.username == "girl")).first()
            if boy and girl and not boy.partner_id:
                boy.partner_id = girl.id
                girl.partner_id = boy.id
                session.add(boy)
                session.add(girl)
                session.commit()

@app.post("/token")
async def login_for_access_token(username: str = Body(..., embed=True), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if not user:
         # Auto create if not exists? Or strict? 
         # User asked for "Boy/Girl" buttons. We seeded them. 
         # So if they send something else, fail.
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@app.get("/")
def read_root():
    return FileResponse('static/index.html')
