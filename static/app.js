/* GRIT Interview Desk demo UI. Data and booking decisions come from /api rather than hardcoded cards. */
let store=null;
let page='home';
let selectedStudent=1;
let selectedInterviewer=1;
let teamFilter='all';
let scheduledDay='';
let saving=false;
const navigation={home:'Student dashboard',booking:'Book an interview',interviewer:'Interviewer schedule',team:'Interview team',preview:'Before & after',rules:'Design decisions'};
const STATE={
 NOT_ELIGIBLE:['Skills not completed','neutral','You need to clear every required skill level before you can book your badge interview.'],
 ELIGIBLE:['Ready to book','positive','You have cleared all the required skills. Book your live interview to earn your Novice badge.'],
 BOOKED:['Interview booked','info','Your interview is confirmed. Check the date, time and interviewer below.'],
 IN_INTERVIEW:['Interview in progress','info','Your interview time has started. The outcome will appear once the interview team saves it.'],
 AWAITING_RESULT:['Awaiting result','warning','Your interview time has ended. The team has not recorded the result yet.'],
 PASSED:['Badge earned','positive','You passed your interview! Your AI Product Mastery Novice badge is now available on your dashboard.'],
 FAILED:['Interview not cleared','danger','Your latest interview result is Fail. The team can advise you about next steps.'],
 RETAKE:['Retake available','warning','Your result is Retake later. Book another slot when you are ready.'],
 NO_SHOW:['Interview missed','warning','Your interview was marked as missed. You may book another available slot in this demo.'],
 ON_HOLD:['Booking on hold','warning','Your account is on hold. Please contact the interview team.'],
 REVOKED:['Badge nullified','danger','A confirmed malpractice flag has nullified this badge. Contact the interview team for details.']
};
const esc=(s='')=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(s,options={})=>new Date(s).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',...options});
const dateLabel=s=>fmt(s,{weekday:'long',day:'numeric',month:'long'});
const shortDate=s=>fmt(s,{day:'numeric',month:'short'});
const clock=s=>fmt(s,{hour:'numeric',minute:'2-digit',hour12:true});
const dateKey=s=>fmt(s,{year:'numeric',month:'2-digit',day:'2-digit'}).split('/').reverse().join('-');
const fullTime=s=>`${dateLabel(s)} · ${clock(s)} IST`;
function status(state){const item=STATE[state]||[state,'neutral',''];return `<span class="status ${item[1]}">● ${item[0]}</span>`}
function showToast(message,err=false){const t=document.getElementById('toast');t.textContent=message;t.className=`toast show${err?' error':''}`;clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>t.className='toast',3600)}
async function request(path,options={}){
 const res=await fetch(path,{headers:{'Content-Type':'application/json'},...options});
 let data={};try{data=await res.json()}catch{}
 if(!res.ok)throw new Error(typeof data.detail==='string'?data.detail:'Something went wrong. Please try again.');
 return data;
}
async function load(){try{store=await request(`/api/state?student_id=${selectedStudent}`);if(!store.interviewers.find(i=>i.id===selectedInterviewer))selectedInterviewer=store.interviewers[0].id;render();}catch(err){document.getElementById('content').innerHTML=`<div class="card pad">Unable to load this demo. ${esc(err.message)}</div>`}}
async function mutate(path,method='POST',payload){if(saving)return;try{saving=true;const out=await request(path,{method,...(payload!==undefined?{body:JSON.stringify(payload)}:{})});showToast(out.message||'Saved. The dashboard has been updated.');await load()}catch(err){showToast(err.message,true)}finally{saving=false}}
function goto(target){page=target;render();window.scrollTo({top:0,behavior:'smooth'})}
function switchPerson(id){selectedStudent=Number(id);load()}
function header(kicker,title,description,action=''){return `<div class="heading-row"><div><div class="eyebrow">${kicker}</div><h1 class="page-title">${title}</h1><p class="lead">${description}</p></div>${action}</div>`}
function render(){
 const n=document.getElementById('nav');n.querySelectorAll('.nav-link').forEach(x=>x.classList.toggle('active',x.dataset.page===page));
 document.getElementById('breadcrumb').textContent=navigation[page];
 const picker=document.getElementById('studentPicker');picker.innerHTML=store.students.map(p=>`<option value="${p.student.id}" ${p.student.id===selectedStudent?'selected':''}>${esc(p.student.name)}</option>`).join('');
 const content=document.getElementById('content');
 content.innerHTML=({home:homePage,booking:bookingPage,interviewer:interviewerPage,team:teamPage,preview:previewPage,rules:rulesPage}[page]||homePage)();
}
function homePage(){
 const {person,track}=store,p=person.student,st=person.state,b=person.booking;
 const currentMessage=st==='BOOKED'&&b?`Your interview is confirmed for ${shortDate(b.start_at)} at ${clock(b.start_at)} IST. You can view or change your booking here.`:STATE[st][2];
 const passed=st==='PASSED',revoked=st==='REVOKED';
 const headline=passed?'You did it. Your badge is unlocked.':revoked?'Your badge needs attention.':st==='BOOKED'?'Your interview is on the calendar.':st==='NOT_ELIGIBLE'?'Your next milestone starts with your skills.':'You are one interview away from your badge.';
 const message=passed?'You completed the required skill levels and cleared the live interview.':revoked?'This badge was nullified following a confirmed policy flag.':st==='BOOKED'?'Everything is booked. You can review your interview details below.':st==='NOT_ELIGIBLE'?'Complete the required skill contests to unlock booking.':'Your required skills are complete. Choose a time that works for you.';
 const cta=st==='ELIGIBLE'||st==='RETAKE'||st==='NO_SHOW'?`<button class="button" data-action="goto" data-target="booking">Choose a time &nbsp; →</button>`:
    ['BOOKED','IN_INTERVIEW','AWAITING_RESULT'].includes(st)?`<button class="button" data-action="goto" data-target="booking">View booking &nbsp; →</button>`:`<button class="button" data-action="goto" data-target="preview">View journey &nbsp; →</button>`;
 const phase=passed?100:st==='NOT_ELIGIBLE'?33:['BOOKED','IN_INTERVIEW','AWAITING_RESULT'].includes(st)?75:st==='REVOKED'?100:66;
 return `${header('STUDENT SPACE',`Good to see you, ${esc(p.name.split(' ')[0])}.`,'Your AI Product Mastery badge progress, all in one place.',status(st))}
 <div class="hero"><div class="hero-text"><div class="eyebrow" style="color:#b8abff;margin-bottom:9px">YOUR NEXT MILESTONE</div><h2>${headline}</h2><p>${message}</p></div>${cta}</div>
 <div class="metrics"><div class="metric"><span class="metric-icon">✦</span><small>Track</small><strong style="font-size:17px;margin-top:10px">AI Product</strong><small>Mastery</small></div><div class="metric"><span class="metric-icon">▣</span><small>Badge level</small><strong style="font-size:23px">Novice</strong><small>First badge in track</small></div><div class="metric"><span class="metric-icon">✓</span><small>Required skills</small><strong>${p.skill