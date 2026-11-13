# GRIT Interview Scheduling

This is my Round 1 assignment for the AI Product Engineer role at NxtWave. The idea is to handle the interview stage after a GRIT student finishes the skills needed for a track badge.

The prototype uses the AI Product Mastery (Novice) badge as an example. Students can book a slot, interviewers can add available times and record results, and the interview team can check who has booked and who is still waiting. The student dashboard updates when the interview is booked or a result is recorded.

## Run locally

You'll need Python 3. From the project folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser. On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Try the demo

Select Aanya Sharma and book an interview. Then open **Interviewer schedule**, record a Pass result, and return to her dashboard to see the badge appear. The student selector has other sample cases, including retakes and a revoked badge. **Reset demo data** returns the app to its starting state.

## A few implementation notes

The backend uses FastAPI and SQLite; the interface is plain HTML, CSS and JavaScript. SQLite transactions and unique indexes prevent two active bookings for one slot. Interview results are kept separately from badge awards, so revoking a badge does not erase the earlier result.

To run the tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

This is a demo with fictional students, not a live NIAT integration. It has no real sign-in, meeting links or notifications. The full design and assumptions are in [the write-up](GRIT_Interview_Design_Writeup.md).
