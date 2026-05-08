import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Set env vars for tests
os.environ['ADMIN_TOKEN'] = 'admintest'
os.environ['WEBHOOK_SECRET'] = 'hooksecret'

def test_admin_requires_token():
    r = client.get('/admin/system')
    assert r.status_code == 401
    r = client.get('/admin/system', headers={'X-Admin-Token':'admintest'})
    assert r.status_code == 200

def test_webhook_secret():
    # missing or bad secret is rejected
    r = client.post('/webhook', json={'symbol':'TCS','action':'BUY','quantity':1,'secret':'bad'})
    assert r.status_code == 401
    r = client.post('/webhook', json={'symbol':'TCS','action':'BUY','quantity':1,'secret':'hooksecret'})
    # may return 400 because no active broker configured, but should not be 401
    assert r.status_code in (200, 400)
