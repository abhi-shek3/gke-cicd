from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import List
import os
import redis
from fastapi.middleware.cors import CORSMiddleware

# Add this near your fake_notes_db variable
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# --- Configuration ---
# This MUST match the secret in the auth-service to validate the signature
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-dev-key")
ALGORITHM = "HS256"

app = FastAPI(title="Notes Service", root_path="/api/notes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# This tells FastAPI to look for an "Authorization: Bearer <token>" header
security = HTTPBearer()

# --- Dummy Database ---
fake_notes_db = []
note_id_counter = 1

# --- Pydantic Models ---
class NoteCreate(BaseModel):
    content: str

class NoteResponse(BaseModel):
    id: int
    owner: str
    content: str

# --- Dependency: Verify Token ---
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extracts the JWT from the header, decodes it, and returns the username."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/notes", response_model=NoteResponse)
def create_note(note: NoteCreate, username: str = Depends(verify_token)):
    global note_id_counter
    new_note = {"id": note_id_counter, "owner": username, "content": note.content}
    fake_notes_db.append(new_note)
    note_id_counter += 1
    try:
        redis_client.publish("note_events", f"User '{username}' created a note: {note.content[:20]}...")
    except Exception as e:
        print(f"Warning: Could not publish to Redis: {e}")
        
    return new_note

@app.get("/notes", response_model=List[NoteResponse])
def get_notes(username: str = Depends(verify_token)):
    # Only return notes that belong to the user who owns the token
    user_notes = [note for note in fake_notes_db if note["owner"] == username]
    return user_notes

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, username: str = Depends(verify_token)):
    global fake_notes_db
    for i, note in enumerate(fake_notes_db):
        if note["id"] == note_id and note["owner"] == username:
            del fake_notes_db[i]
            return {"message": "Note deleted successfully"}
    raise HTTPException(status_code=404, detail="Note not found or unauthorized")

