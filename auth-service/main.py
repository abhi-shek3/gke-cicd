from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os

# --- Configuration ---
# Note: In Phase 4, we will move this secret to a K8s Secret!
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-dev-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title="Auth Service", root_path="/api/auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Security Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Dummy Database ---
fake_users_db = {}

# --- Pydantic Models (Schemas) ---
class UserAuth(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Helper Functions ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Endpoints ---
@app.get("/health")
def health_check():
    """Health check endpoint for K8s probes later on."""
    return {"status": "ok"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserAuth):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password
    }
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(user: UserAuth):
    db_user = fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}