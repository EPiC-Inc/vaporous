from datetime import datetime, timedelta
from threading import Lock
from uuid import uuid4

#TODO - implement in redis?
SESSIONS = {}
SESSION_EXPIRY = timedelta(hours=24)

def login(username: str, password: str | bytes):
    # Prevents duplicate uuids just in case
    while SESSIONS.get(id := str(uuid4())):
        pass
    SESSIONS[id] = (username, datetime.now() + SESSION_EXPIRY)

def get_session(session_id: str):
    if not (session := SESSIONS.get(session_id)):
        return None
    username, expiry = session
    if expiry < datetime.now():
        return None
