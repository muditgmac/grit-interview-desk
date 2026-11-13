from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
import app as mod

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "test.db")
    mod.init_db()
    return TestClient(mod.app)

def book(client, student, slot):
    return client.post("/api/bookings", json={"student_id":student,"slot_id":slot})

def test_eligibility_and_booking(client):
    r=book(client,4,5)
    assert r.status_code==409
    r=book(client,1,5)
    assert r.status_code==200
    assert client.get('/api/state?student_id=1').json()['person']['state']=='BOOKED'
    assert book(client,5,5).status_code==409
    assert book(client,1,6).status_code==409

def test_atomic_double_booking(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda args: book(client,*args).status_code,[(1,6),(5,6)]))
    assert sorted(results)==[200,409]
    data=client.get('/api/state').json()
    assert sum(1 for b in data['bookings'] if b['slot_id']==6 and b['status']=='BOOKED')==1

def test_cancel_then_rebook(client):
    assert book(client,1,5).status_code==200
    booked=client.get('/api/state?student_id=1').json()['person']['booking']
    assert client.post(f"/api/bookings/{booked['id']}/cancel",json={"student_id":1}).status_code==200
    assert book(client,5,5).status_code==200

def test_pass_and_revoke(client):
    assert book(client,1,5).status_code==200
    bid=client.get('/api/state?student_id=1').json()['person']['booking']['id']
    assert client.post(f'/api/bookings/{bid}/outcome',json={'outcome':'PASS','notes':'Clear explanation'}).status_code==200
    assert client.get('/api/state?student_id=1').json()['person']['state']=='PASSED'
    assert client.post('/api/malpractice',json={'student_id':1,'reason':'Confirmed malpractice report'}).status_code==200
    p=client.get('/api/state?student_id=1').json()['person']
    assert p['state']=='REVOKED' and p['badge']['state']=='REVOKED'
    assert book(client,1,7).status_code==409

def test_retake_and_protected_slot(client):
    assert client.get('/api/state?student_id=5').json()['person']['state']=='RETAKE'
    assert book(client,5,5).status_code==200
    assert client.delete('/api/slots/5').status_code==409
    assert client.post('/api/malpractice',json={'student_id':4,'reason':'Confirmed flag'}).status_code==409

def test_no_overlap(client):
    s=client.get('/api/state').json()['slots'][4]
    start=s['start_at']
    assert client.post('/api/slots',json={'interviewer_id':s['interviewer_id'],'start_at':start}).status_code==409
