"""GRIT Interview Desk: compact FastAPI + SQLite proof-of-concept.

All identities are seeded demo accounts and role selection is deliberately NOT authentication.
For production, replace demo identity switch with NIAT SSO and role-based permissions.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("GRIT_DB_PATH", str(ROOT / "grit_demo.db")))
IST = ZoneInfo("Asia/Kolkata")
BADGE_ID = 1
app = FastAPI(title="GRIT Interview Desk - assignment prototype", version="1.0")

@contextmanager
def db(write=False):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        if write:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        if write:
            conn.execute("COMMIT")
    except Exception:
        if write:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def now():
    return datetime.now(IST)

def when(days=1, hour=10, minute=0):
    d = now().date() + timedelta(days=days)
    return datetime.combine(d, time(hour, minute), IST).isoformat()

def rowdict(rows):
    if rows is None: return None
    if isinstance(rows, sqlite3.Row): return dict(rows)
    return [dict(r) for r in rows]

def audit(conn, action, detail, actor="demo"):
    conn.execute("INSERT INTO audit_log(created_at,actor,action,details) VALUES(?,?,?,?)", (now().isoformat(), actor, action, detail))

def init_db():
    # executescript manages its own transaction; seed a fresh local demo DB.
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS students(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          cohort TEXT NOT NULL, skills_complete INTEGER NOT NULL DEFAULT 0 CHECK(skills_complete IN(0,1)),
          policy_hold INTEGER NOT NULL DEFAULT 0 CHECK(policy_hold IN(0,1))
        );
        CREATE TABLE IF NOT EXISTS interviewers(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialty TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS badges(
          id INTEGER PRIMARY KEY, track_name TEXT NOT NULL, level TEXT NOT NULL,
          skill_requirements TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS badge_awards(
          student_id INTEGER NOT NULL REFERENCES students(id), badge_id INTEGER NOT NULL REFERENCES badges(id),
          state TEXT NOT NULL CHECK(state IN('EARNED','REVOKED')),
          earned_at TEXT NOT NULL, revoked_at TEXT, reason TEXT,
          PRIMARY KEY(student_id,badge_id)
        );
        CREATE TABLE IF NOT EXISTS slots(
          id INTEGER PRIMARY KEY AUTOINCREMENT, interviewer_id INTEGER NOT NULL REFERENCES interviewers(id),
          start_at TEXT NOT NULL, end_at TEXT NOT NULL, is_open INTEGER NOT NULL DEFAULT 1,
          UNIQUE(interviewer_id, start_at)
        );
        CREATE TABLE IF NOT EXISTS bookings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id),
          badge_id INTEGER NOT NULL REFERENCES badges(id), slot_id INTEGER NOT NULL REFERENCES slots(id),
          status TEXT NOT NULL CHECK(status IN('BOOKED','CANCELLED','COMPLETED')),
          outcome TEXT CHECK(outcome IN('PASS','FAIL','RETAKE','NO_SHOW') OR outcome IS NULL),
          notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          CHECK((status = 'COMPLETED' AND outcome IS NOT NULL) OR
                (status != 'COMPLETED' AND outcome IS NULL))
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_slot ON bookings(slot_id) WHERE status='BOOKED';
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_student_badge ON bookings(student_id,badge_id) WHERE status='BOOKED';
        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, actor TEXT NOT NULL,
          action TEXT NOT NULL, details TEXT NOT NULL
        );
        """)
        if c.execute("SELECT COUNT(*) FROM students").fetchone()[0]:
            return
        c.executemany("INSERT INTO students(id,name,email,cohort,skills_complete,policy_hold) VALUES(?,?,?,?,?,?)", [
          (1,"Aanya Sharma","aanya@demo.niat", "2025",1,0),
          (2,"Kabir Mehta","kabir@demo.niat", "2024",1,0),
          (3,"Mira Nair","mira@demo.niat", "2024",1,0),
          (4,"Dev Patel","dev@demo.niat", "2025",0,0),
          (5,"Ishaan Rao","ishaan@demo.niat", "2023",1,0),
          (6,"Sara Khan","sara@demo.niat", "2025",1,1),
          (7,"Neha Singh","neha@demo.niat", "2024",1,0)
        ])
        c.executemany("INSERT INTO interviewers(id,name,specialty) VALUES(?,?,?)", [
          (1,"Riya Kapoor","AI Product Mastery"),(2,"Arjun Nair","AI Product Mastery")
        ])
        c.execute("INSERT INTO badges VALUES(1,?,?,?)", ("AI Product Mastery","Novice","Computational Thinking L1; CS Fundamentals L1; Applied Gen AI Development L1; UI Engineering L2"))
        for day in (1,2,3,4):
            for hr, m, interviewer in [(10,0,1),(11,0,1),(14,0,2),(15,0,2)]:
                start = when(day,hr,m)
                end = (datetime.fromisoformat(start)+timedelta(minutes=30)).isoformat()
                c.execute("INSERT INTO slots(interviewer_id,start_at,end_at) VALUES(?,?,?)", (interviewer,start,end))
        # A few seeded stages, all tied to actual rows rather than screen-specific mockups.
        def seeded_booking(student, slot, status, outcome=None):
            ts = now().isoformat()
            c.execute("INSERT INTO bookings(student_id,badge_id,slot_id,status,outcome,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (student,1,slot,status,outcome,ts,ts))
        seeded_booking(2,1,"BOOKED")
        seeded_booking(3,2,"COMPLETED","PASS")
        seeded_booking(5,3,"COMPLETED","RETAKE")
        seeded_booking(7,4,"COMPLETED","PASS")
        c.execute("UPDATE slots SET is_open=0 WHERE id IN (2,3,4)")
        c.execute("INSERT INTO badge_awards(student_id,badge_id,state,earned_at,revoked_at,reason) VALUES(?,?,?,?,?,?)", (3,1,"EARNED",now().isoformat(),None,None))
        c.execute("INSERT INTO badge_awards(student_id,badge_id,state,earned_at,revoked_at,reason) VALUES(?,?,?,?,?,?)", (7,1,"REVOKED",now().isoformat(),now().isoformat(),"Confirmed malpractice flag"))
        audit(c,"DEMO_INITIALISED","Sample records created")


def latest_booking(c, sid):
    return c.execute("""SELECT b.*,s.start_at,s.end_at,i.name as interviewer_name
       FROM bookings b JOIN slots s ON b.slot_id=s.id JOIN interviewers i ON s.interviewer_id=i.id
       WHERE b.student_id=? AND b.badge_id=? ORDER BY b.id DESC LIMIT 1""", (sid,BADGE_ID)).fetchone()

def student_state(c, sid):
    st=c.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone()
    if not st: raise HTTPException(404,"Student not found")
    award=c.execute("SELECT * FROM badge_awards WHERE student_id=? AND badge_id=?",(sid,BADGE_ID)).fetchone()
    booking=latest_booking(c,sid)
    if award and award['state']=='REVOKED': state='REVOKED'
    elif st['policy_hold']: state='ON_HOLD'
    elif award and award['state']=='EARNED': state='PASSED'
    elif not st['skills_complete']: state='NOT_ELIGIBLE'
    elif booking and booking['status']=='BOOKED':
        if datetime.fromisoformat(booking['start_at'])>now(): state='BOOKED'
        elif datetime.fromisoformat(booking['end_at'])>now(): state='IN_INTERVIEW'
        else: state='AWAITING_RESULT'
    elif booking and booking['status']=='COMPLETED':
        state={'PASS':'PASSED','FAIL':'FAILED','RETAKE':'RETAKE','NO_SHOW':'NO_SHOW'}[booking['outcome']]
    elif booking and booking['status']=='CANCELLED': state='ELIGIBLE'
    else: state='ELIGIBLE'
    return {"student":rowdict(st),"badge":rowdict(award),"booking":rowdict(booking),"state":state}

class BookRequest(BaseModel):
    student_id:int
    slot_id:int
class CancelRequest(BaseModel):
    student_id:int
class SlotRequest(BaseModel):
    interviewer_id:int
    start_at:str
class OutcomeRequest(BaseModel):
    outcome:str
    notes:str=""
class FlagRequest(BaseModel):
    student_id:int
    reason:str=Field(min_length=5,max_length=240)

@app.get("/")
def home(): return FileResponse(ROOT/'static'/'index.html')
@app.get("/static/{filename}")
def assets(filename:str):
    if filename not in ("styles.css","app.js"): raise HTTPException(404)
    return FileResponse(ROOT/'static'/filename)

@app.get("/api/state")
def state(student_id:int=1):
    with db() as c:
        person=student_state(c,student_id)
        all_students=[student_state(c,r['id']) for r in c.execute('SELECT id FROM students ORDER BY id').fetchall()]
        slot_rows = c.execute("""SELECT s.*,i.name AS interviewer_name,
           b.id AS booking_id,b.student_id AS booked_by,b.status AS booking_status,
           b.outcome AS booking_outcome, st.name AS student_name
           FROM slots s JOIN interviewers i ON i.id=s.interviewer_id
           LEFT JOIN bookings b ON b.slot_id=s.id AND b.status='BOOKED'
           LEFT JOIN students st ON st.id=b.student_id
           ORDER BY s.start_at,i.id""").fetchall()
        all_bookings=c.execute("""SELECT b.*,st.name AS student_name,i.name AS interviewer_name,
              s.start_at,s.end_at,s.interviewer_id
              FROM bookings b JOIN students st ON st.id=b.student_id
              JOIN slots s ON s.id=b.slot_id JOIN interviewers i ON i.id=s.interviewer_id
              ORDER BY b.id DESC""").fetchall()
        events=c.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT 12').fetchall()
        return {"now":now().isoformat(),"person":person,"students":all_students,
                "interviewers":rowdict(c.execute('SELECT * FROM interviewers ORDER BY id').fetchall()),
                "slots":rowdict(slot_rows),"bookings":rowdict(all_bookings),
                "audit":rowdict(events),"track":rowdict(c.execute('SELECT * FROM badges WHERE id=?',(BADGE_ID,)).fetchone())}

@app.post("/api/bookings")
def book(req:BookRequest):
    with db(write=True) as c:
        state=student_state(c,req.student_id)
        if state['state'] not in ('ELIGIBLE','RETAKE','NO_SHOW'):
            raise HTTPException(409,"This student is not currently allowed to book another interview.")
        slot=c.execute("SELECT * FROM slots WHERE id=?",(req.slot_id,)).fetchone()
        if not slot or not slot['is_open']: raise HTTPException(404,"Slot is unavailable.")
        if datetime.fromisoformat(slot['start_at']) <= now(): raise HTTPException(409,"That slot is already in the past.")
        try:
            ts=now().isoformat()
            c.execute("INSERT INTO bookings(student_id,badge_id,slot_id,status,created_at,updated_at) VALUES(?,?,?,'BOOKED',?,?)",(req.student_id,BADGE_ID,req.slot_id,ts,ts))
        except sqlite3.IntegrityError:
            raise HTTPException(409,"That time was just taken. Please choose another slot.")
        audit(c,"BOOKED",f"Student {req.student_id} booked slot {req.slot_id}",f"student:{req.student_id}")
    return {"ok":True,"message":"Your interview is booked."}

@app.post("/api/bookings/{booking_id}/cancel")
def cancel(booking_id:int,req:CancelRequest):
    with db(write=True) as c:
        b=c.execute("SELECT b.*,s.start_at FROM bookings b JOIN slots s ON s.id=b.slot_id WHERE b.id=?",(booking_id,)).fetchone()
        if not b or b['student_id']!=req.student_id or b['status']!='BOOKED': raise HTTPException(409,"Only your active booking can be cancelled.")
        # For the demo: disallow changes within 2h of interview; admin rescheduling is out of scope.
        if datetime.fromisoformat(b['start_at']) <= now()+timedelta(hours=2):
            raise HTTPException(409,"Please contact the interview team to change a slot within two hours of start.")
        c.execute("UPDATE bookings SET status='CANCELLED', updated_at=? WHERE id=?",(now().isoformat(),booking_id))
        audit(c,"CANCELLED",f"Booking {booking_id} cancelled",f"student:{req.student_id}")
    return {"ok":True}

@app.post("/api/slots")
def make_slot(req:SlotRequest):
    try:
        start=datetime.fromisoformat(req.start_at)
        if start.tzinfo is None: start=start.replace(tzinfo=IST)
        start=start.astimezone(IST)
    except ValueError: raise HTTPException(422,"Invalid date/time")
    if start<now(): raise HTTPException(409,"Availability must be in the future.")
    if start.minute not in (0,30): raise HTTPException(422,"Use half-hour increments.")
    end=start+timedelta(minutes=30)
    with db(write=True) as c:
        if not c.execute('SELECT 1 FROM interviewers WHERE id=?',(req.interviewer_id,)).fetchone(): raise HTTPException(404,"Interviewer missing")
        overlaps=c.execute('''SELECT 1 FROM slots WHERE interviewer_id=? AND is_open=1
        AND start_at < ? AND end_at > ? LIMIT 1''',(req.interviewer_id,end.isoformat(),start.isoformat())).fetchone()
        if overlaps: raise HTTPException(409,"This interviewer already has availability at that time.")
        c.execute('INSERT INTO slots(interviewer_id,start_at,end_at) VALUES(?,?,?)',(req.interviewer_id,start.isoformat(),end.isoformat()))
        audit(c,"SLOT_ADDED",f"Interviewer {req.interviewer_id} added {start.isoformat()}",f"interviewer:{req.interviewer_id}")
    return {"ok":True}

@app.delete("/api/slots/{slot_id}")
def remove_slot(slot_id:int):
    with db(write=True) as c:
        slot=c.execute('SELECT * FROM slots WHERE id=?',(slot_id,)).fetchone()
        if not slot: raise HTTPException(404,"Slot missing")
        if c.execute("SELECT 1 FROM bookings WHERE slot_id=? AND status='BOOKED'",(slot_id,)).fetchone():
            raise HTTPException(409,"This slot is booked. Contact the interview team to reschedule the student first.")
        c.execute("UPDATE slots SET is_open=0 WHERE id=?",(slot_id,))
        audit(c,"SLOT_REMOVED",f"Slot {slot_id} closed",f"interviewer:{slot['interviewer_id']}")
    return {"ok":True}

@app.post("/api/bookings/{booking_id}/outcome")
def set_outcome(booking_id:int, req:OutcomeRequest):
    result=req.outcome.upper()
    if result not in ('PASS','FAIL','RETAKE','NO_SHOW'): raise HTTPException(422,"Choose pass, fail, retake or no-show")
    with db(write=True) as c:
        b=c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone()
        if not b or b['status']!='BOOKED': raise HTTPException(409,"Only active interviews can receive a result.")
        c.execute("UPDATE bookings SET status='COMPLETED',outcome=?,notes=?,updated_at=? WHERE id=?",(result,req.notes.strip()[:600],now().isoformat(),booking_id))
        c.execute("UPDATE slots SET is_open=0 WHERE id=?",(b['slot_id'],))
        if result=='PASS':
            c.execute("INSERT INTO badge_awards(student_id,badge_id,state,earned_at) VALUES(?,?,'EARNED',?) ON CONFLICT(student_id,badge_id) DO UPDATE SET state='EARNED',earned_at=excluded.earned_at,revoked_at=NULL,reason=NULL",(b['student_id'],BADGE_ID,now().isoformat()))
        audit(c,"RESULT_RECORDED",f"Booking {booking_id}: {result}","interview-team")
    return {"ok":True}

@app.post("/api/malpractice")
def flag(req:FlagRequest):
    with db(write=True) as c:
        p=c.execute('SELECT * FROM students WHERE id=?',(req.student_id,)).fetchone()
        if not p: raise HTTPException(404,"Student missing")
        if not c.execute("SELECT 1 FROM badge_awards WHERE student_id=? AND badge_id=? AND state='EARNED'",(req.student_id,BADGE_ID)).fetchone():
            raise HTTPException(409,"Only an awarded badge can be revoked in this demo.")
        c.execute("UPDATE badge_awards SET state='REVOKED',revoked_at=?,reason=? WHERE student_id=? AND badge_id=?",(now().isoformat(),req.reason,BADGE_ID,req.student_id))
        c.execute("UPDATE students SET policy_hold=1 WHERE id=?",(req.student_id,))
        audit(c,"BADGE_REVOKED",f"Student {req.student_id}: {req.reason}","interview-team")
    return {"ok":True}

@app.post("/api/reset")
def reset():
    """Demo-only reset; remove entirely before a real deployment."""
    if os.environ.get("GRIT_ALLOW_DEMO_RESET","1")!="1": raise HTTPException(403,"Reset disabled")
    if DB_PATH.exists(): DB_PATH.unlink()
    init_db()
    return {"ok":True}

init_db()
