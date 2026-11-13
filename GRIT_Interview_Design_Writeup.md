# GRIT interview scheduling

AI Product Engineer | Round 1 design note

The feature I designed connects three activities: students book an interview once their required skills are cleared, interviewers manage available times and record the result, and the interview team sees who is still waiting to book. The student dashboard changes after booking, after the result and if a previously earned badge is revoked. I used AI Product Mastery / Novice as the example, with 30-minute interviews and fictional student accounts.

## 1. Student journey

| Stage | What changes it |
| --- | --- |
| Not eligible / On hold | Skills incomplete or a policy hold is active. Completing the requirements, or clearing the hold, makes booking possible. |
| Ready to book | All required skills cleared, with no active booking. Reserving an open slot moves the student to Booked. |
| Booked | Confirmed slot appears on the dashboard. Cancellation returns the student to Ready to book; at the start time, the status changes to In interview. |
| In interview / Awaiting result | The scheduled interval starts, then ends. These are time-based display states until an interviewer saves a result. |
| Passed / Badge earned | The team records Pass. An award is created and the student sees the badge on the home screen. |
| Failed / Retake later / No-show | The result is recorded and shown to the student. The demo permits rebooking after Retake or No-show, not automatically after Fail. |
| Badge revoked | Following a confirmed malpractice decision, staff revoke the award. The earlier Pass is still kept in the history. |

A reschedule is treated as cancelling one booking and making another. I keep earlier attempts instead of replacing them, so the team can see what happened.

## 2. Edge cases and assumptions

| Situation | Decision / point to confirm |
| --- | --- |
| Two students select one time | The database allows only one active booking for that slot. The other student is asked to choose again. |
| Repeat booking or slot removal | One active booking per student and badge. A slot with an active booking cannot be removed by an interviewer. |
| Cancellation or overlapping times | The demo allows cancellation until two hours before the interview and checks interviewer-slot overlaps. Emergency changes need team help. |
| Missed interviews and retakes | No-show and Retake later are separate results. NIAT would need to set retry limits, waiting periods and who approves another attempt. |
| Eligibility or malpractice changes | Production should re-check NIAT eligibility before the interview. Badge revocation needs a confirmed decision and a review or appeal process. |

## 3. Data model and booking safety

The prototype uses SQLite. It has enough information to demonstrate a student booking, an interviewer recording an outcome and a badge being revoked. The important tables are:

| Table | Main fields and purpose |
| --- | --- |
| students | id, name, email, cohort, skills_complete, policy_hold. Sample eligibility is stored here. |
| badges / interviewers | Badge track, level and requirement text; interviewer id, name and specialty. |
| slots | id, interviewer_id, start_at, end_at, is_open. A slot belongs to one interviewer. |
| bookings | id, student_id, badge_id, slot_id, status, outcome, notes, created_at, updated_at. Each attempt is a separate record. |
| badge_awards | student_id, badge_id, state, earned_at, revoked_at, reason. The award can change to Revoked without deleting a Pass. |
| audit_log | id, created_at, actor, action, details. Records booking, cancellation, result and revocation events. |

When someone clicks Book, the server opens a SQLite write transaction (BEGIN IMMEDIATE), checks eligibility and slot availability, and inserts the booking. Two partial unique indexes enforce one active booking per slot and one active booking per student per badge. I used the database constraint because two people can click the same time before either browser refreshes. A real deployment would need authenticated roles and persistent storage; the current demo has neither.

## 4. Screens and student messages

The working prototype has a student home screen, available-slot picker, interviewer schedule with an outcome form, team queue, and before/after examples. The home screen starts with a booking prompt; after Pass it shows “Badge earned”; after a confirmed malpractice flag it shows the badge as revoked.

“You have cleared all the required skills. Book your live interview to earn your Novice badge.”

“Your interview is confirmed for [date] at [time] IST. You can view or change your booking here.”

“You passed your interview! Your AI Product Mastery Novice badge is now available on your dashboard.”

## 5. What I would check before a real launch

NIAT needs to confirm the rules for failed interviews, rescheduling, no-shows, retake limits and malpractice appeals. The live product would also need NIAT sign-in, interviewer permissions, video links, reminders and a database that survives restarts. The demo intentionally allows recording a result before the appointment time so that the full flow can be shown; production should restrict that.

References: GRIT official How GRIT Works, Rules, and Tracks & Badge Progression (checked 13 November 2026).
