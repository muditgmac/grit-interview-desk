# GRIT Interview Scheduling

I built this prototype for the AI Product Engineer Round 1 assignment at NxtWave. The problem is to manage the interview stage of GRIT, after a student completes the skills required for a track badge.

A student should be able to find an available time without contacting the interview team. At the same time, interviewers need a way to manage their schedules and record results. I have tried to keep these steps connected so that the student's dashboard reflects what has happened without someone updating it separately.

## What the prototype covers

The student dashboard shows the badge requirements, interview status and latest result. An eligible student can choose a 30-minute interview slot, confirm a booking and see the details on the dashboard.

The interviewer view shows scheduled interviews for a selected date. Interviewers can add availability and record a result as **Pass**, **Fail** or **Retake later**. I also added **No-show** to cover missed interviews. The interview team view shows eligible students who have or have not booked, along with recent changes.

I included separate before-and-after screens because I wanted to show how the same dashboard changes once a student books an interview or earns a badge. There is also a sample case where an awarded badge is later revoked following a confirmed malpractice flag.

For now, the demo focuses on the **AI Product Mastery / Novice** badge. The sample records are fictional.

## How I handled booking conflicts

A slot should not be booked by two students, even if both click on it at almost the same time. I used SQLite transactions and a unique index on active bookings for this. The database accepts the first valid booking and rejects the other one. I also prevent a student from holding two active bookings for the same badge.

Interview results and badge awards are stored separately. This means a student's interview history is still available if an earned badge is later revoked. The system does not treat revocation as though the student never passed the interview.

## Running it locally

You need Python 3 installed. On a Mac, you can open `START_MAC.command` from the extracted project folder. The script installs the Python dependencies and starts the server.

You can also run it from Terminal:

```bash
cd grit_interview_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in a browser. Keep Terminal open while using the application. Press `Ctrl+C` to stop the server.

On Windows, use `START_WINDOWS.bat` after installing Python.

## A quick way to test the flow

Start with **Aanya Sharma**, who has completed the required skills but has not booked an interview. Book a slot for her, then open **Interviewer schedule** and record a Pass result. When you return to her dashboard, the interview status and badge should have changed.

The student selector also has examples of a booked interview, a passed interview, a retake, an ineligible student, a student on hold and a revoked badge. Use **Reset demo data** to return to the original sample records.

To run the automated checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Tools used

- **Backend:** Python and FastAPI
- **Database:** SQLite
- **Interface:** HTML, CSS and JavaScript
- **Deployment configuration:** `render.yaml` for an optional Render demonstration

## What is not included

This is an assignment prototype, not a connection to NIAT's live systems. There is no real login, interviewer authentication, meeting-link generation, email or SMS notification, or connection to actual skill-clearance records. Switching between sample students and interviewer views is only for testing.

The demo also lets an interviewer record a result before the scheduled interview time, so that the complete flow can be demonstrated. In a real system, I would restrict this and add role-based permissions, clearer cancellation and rescheduling rules, and proper timezone handling. SQLite data on a free hosted service may be reset after a restart, so the public version should be treated as a temporary demonstration rather than persistent storage.

The GRIT rules and badge requirements were referenced from the [official GRIT overview](https://www.grit.niatindia.com/how-grit-works), [badge progression](https://www.grit.niatindia.com/tracks-badge-progression) and [rules page](https://www.grit.niatindia.com/rules).
