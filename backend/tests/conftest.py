import os
import tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'tests.db').replace('\\','/')
os.environ['DEMO_PASSWORD']='test-only-password-unique'
os.environ['BANK_A_REGISTRATION_INVITE']='test-invite'
os.environ['DEMO']='true'
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, limits
from backend.app.core import Session, Base, engine

@pytest.fixture()
def clients():
    limits.clear()
    Base.metadata.drop_all(engine)
    with TestClient(app) as a, TestClient(app) as b:
        a.post('/api/auth/login',json={'email':'bank_a@federguard.demo','password':os.environ['DEMO_PASSWORD']})
        b.post('/api/auth/login',json={'email':'bank_b@federguard.demo','password':os.environ['DEMO_PASSWORD']})
        yield a,b
