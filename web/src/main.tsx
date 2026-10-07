import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {atom,useAtom} from 'jotai';
import {QueryClient,QueryClientProvider,useQuery,useQueryClient} from '@tanstack/react-query';
import './style.css';

const selected=atom<string|null>(null);
const API=import.meta.env.VITE_API_URL||'http://localhost:8000';
const KEY=import.meta.env.VITE_ADMIN_API_KEY||'local-dev-only';
type Slide={id:string;headline:string;body:string;position:number};
type Post={id:string;title:string;caption:string;status:string;version:string;created:string;slides:Slide[]};
async function request(path:string,method='GET',body?:unknown){
 const r=await fetch(API+path,{method,headers:{'Content-Type':'application/json','X-API-Key':KEY},body:body?JSON.stringify(body):undefined});
 if(!r.ok){const data=await r.json().catch(()=>({detail:'Request failed'}));throw Error(data.detail||'Request failed')}
 return r.json();
}
const sample={title:'Why AI code review still needs humans',caption:'Practical checks for responsible AI-assisted code review. #AIEngineering',slides:[
 {headline:'CAN YOU TRUST AI CODE REVIEW?',body:'A practical guide for engineering teams'},
 {headline:'THE REAL PROBLEM',body:'More comments do not always mean more bugs found.'},
 {headline:'MEASURE WHAT MATTERS',body:'Track true positives, false positives, severity, and actionability.'},
 {headline:'TEST THE EDGE CASES',body:'Authorization boundaries, race conditions, and data leaks.'},
 {headline:'KEEP YOUR QUALITY GATES',body:'Tests, static analysis, security scanning, and human review.'},
 {headline:'START WITH A PILOT',body:'Measure against real historical PRs before rollout.'},
 {headline:'BUILD A FEEDBACK LOOP',body:'Review missed bugs and improve prompts and tooling.'},
 {headline:'SAVE THIS CHECKLIST',body:'Follow for practical AI engineering insights.'}
]};
function App(){
 const qc=useQueryClient();const [id,setId]=useAtom(selected);const [tab,setTab]=useState('Overview');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const [slide,setSlide]=useState(0);const [title,setTitle]=useState('');const [url,setUrl]=useState('');const [excerpt,setExcerpt]=useState('');
 const [editTitle,setEditTitle]=useState('');const [editCaption,setEditCaption]=useState('');const [editHeadline,setEditHeadline]=useState('');const [editBody,setEditBody]=useState('');
 const {data=[],isLoading}=useQuery<Post[]>({queryKey:['posts'],queryFn:()=>request('/posts')});
 const active=data.find(p=>p.id===id);
 function selectPost(p:Post){setId(p.id);setTab('Library');setSlide(0);setEditTitle(p.title);setEditCaption(p.caption);setEditHeadline(p.slides[0]?.headline||'');setEditBody(p.slides[0]?.body||'')}
 function changeSlide(index:number){if(!active)return;setSlide(index);setEditHeadline(active.slides[index]?.headline||'');setEditBody(active.slides[index]?.body||'')}
 async function run(fn:()=>Promise<unknown>){setBusy(true);setError('');try{await fn();await qc.invalidateQueries({queryKey:['posts']})}catch(e){setError(String(e))}finally{setBusy(false)}}
 async function create(){await run(async()=>{const r=await request('/posts','POST',sample);setId(r.id);setTab('Library')})}
 async function generate(){await run(async()=>{const r=await request('/research/generate','POST',{title,url,excerpt});setId(r.id);setTab('Library')})}
 async function transition(action:string){if(active)await run(()=>request('/posts/'+active.id+'/'+action,'POST'))}
 async function download(){if(!active)return;setBusy(true);try{const r=await fetch(API+'/posts/'+active.id+'/export',{headers:{'X-API-Key':KEY}});if(!r.ok)throw Error('Export failed');const blob=await r.blob();const href=URL.createObjectURL(blob);const a=document.createElement('a');a.href=href;a.download='devai-'+active.id+'.zip';a.click();URL.revokeObjectURL(href)}catch(e){setError(String(e))}finally{setBusy(false)}}
 return <div className="shell"><aside><div className="brand"><span className="brandmark">✳</span>devai studio</div><div className="workspace">WORKSPACE</div><nav>{['Overview','Library','Calendar','Analytics','Settings'].map(name=><button key={name} className={tab===name?'nav active':'nav'} onClick={()=>{setTab(name);setId(null)}}>{name}</button>)}</nav><div className="sidefoot">Creator workspace · Private review</div></aside><main><header><span>Workspace / {tab}</span><span>✓ Approval required</span></header><div className="content"><div className="topline"><div><div className="eyebrow">✳ CONTENT INTELLIGENCE</div><h1>{active?'Review content':tab==='Overview'?'Good morning, creator.':tab}</h1><p className="subtitle">Turn emerging AI stories into exceptional content.</p></div><button className="primary" onClick={create} disabled={busy}>+ New draft</button></div>
 {error?<div className="error">{error}</div>:null}
 {!active?<><section className="panel"><h2>Generate a source-backed AI carousel</h2><p className="hint">Paste a verified article excerpt. All generated content requires fact-checking and approval.</p><label>Story headline</label><input value={title} onChange={e=>setTitle(e.target.value)}/><label>Primary source URL</label><input value={url} onChange={e=>setUrl(e.target.value)}/><label>Source excerpt (at least 120 characters)</label><textarea rows={4} value={excerpt} onChange={e=>setExcerpt(e.target.value)}/><button className="primary" disabled={busy||!title.trim()||!url.startsWith('https://')||excerpt.trim().length<120} onClick={generate}>✳ Generate 8-slide draft</button></section><div className="stats"><div className="stat"><span>Total drafts</span><strong>{data.length}</strong></div><div className="stat"><span>Needs review</span><strong>{data.filter(p=>p.status==='pending_review').length}</strong></div><div className="stat"><span>Approved</span><strong>{data.filter(p=>p.status==='approved').length}</strong></div></div><h2>Content library</h2>{isLoading?<p>Loading…</p>:data.length===0?<div className="empty"><h3>Your next great post starts here.</h3><button className="primary" onClick={create}>Create first draft</button></div>:<div className="cards">{data.map(p=><button key={p.id} className="postcard" onClick={()=>selectPost(p)}><div className="cardart"><span>AI / ENGINEERING</span><strong>{p.slides[0]?.headline||p.title}</strong><small>{p.slides.length} SLIDES</small></div><div className="cardinfo"><span className={'pill '+p.status}>{p.status.replace('_',' ')}</span><h3>{p.title}</h3><p>{new Date(p.created).toLocaleDateString()}</p></div></button>)}</div>}</>:
 <><div className="reviewhead"><button className="ghost" onClick={()=>setId(null)}>← Back to library</button><span className={'pill '+active.status}>{active.status}</span></div><div className="reviewgrid"><section className="preview"><div className="slide"><div className="slidekicker">DEVAISTUDIO / AI ENGINEERING</div><div className="slidecenter"><span className="micro">FIELD NOTES · {slide+1}</span><h2>{active.slides[slide]?.headline}</h2><p>{active.slides[slide]?.body}</p></div><div className="slidebottom">BUILD SMARTER. SHIP BETTER. {slide+1} / {active.slides.length}</div></div><div className="slidestrip">{active.slides.map((s,i)=><button key={s.id} className={slide===i?'thumb chosen':'thumb'} onClick={()=>changeSlide(i)}>{i+1}</button>)}</div></section><section className="editor"><div className="panel"><h3>Post details · v{active.version}</h3><label>Headline</label><input value={editTitle} onChange={e=>setEditTitle(e.target.value)}/><label>Caption</label><textarea rows={7} value={editCaption} onChange={e=>setEditCaption(e.target.value)}/><button className="secondary" disabled={busy} onClick={()=>run(()=>request('/posts/'+active.id,'PATCH',{title:editTitle,caption:editCaption}))}>Save post</button></div><div className="panel"><h3>Selected slide</h3><label>Headline</label><input value={editHeadline} onChange={e=>setEditHeadline(e.target.value)}/><label>Body</label><textarea rows={4} value={editBody} onChange={e=>setEditBody(e.target.value)}/><button className="secondary" disabled={busy} onClick={()=>run(()=>request('/posts/'+active.id+'/slides/'+active.slides[slide].id,'PATCH',{headline:editHeadline,body:editBody}))}>Save slide</button><button className="secondary" onClick={download}>Download 1080 × 1350 PNG ZIP</button></div><div className="panel"><h3>Approval workflow</h3><p className="hint">Editing invalidates approval. Instagram publishing requires separate configuration.</p><div className="actions">{active.status==='draft'?<button className="primary" disabled={busy} onClick={()=>transition('submit')}>Submit for review</button>:null}{active.status==='pending_review'?<><button className="primary" disabled={busy} onClick={()=>transition('approve')}>Approve</button><button className="secondary" disabled={busy} onClick={()=>transition('reject')}>Reject</button></>:null}{active.status==='rejected'?<button className="primary" onClick={()=>transition('submit')}>Resubmit</button>:null}</div></div></section></div></>}
 </div></main></div>;
}
createRoot(document.getElementById('root')!).render(<QueryClientProvider client={new QueryClient()}><App/></QueryClientProvider>);
