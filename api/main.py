import os, uuid, datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./devai.db')
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {})
Session=sessionmaker(bind=engine)
Base=declarative_base()
class Post(Base):
 __tablename__='posts'
 id=Column(String,primary_key=True); title=Column(String,nullable=False); caption=Column(Text,default=''); status=Column(String,default='draft'); version=Column(String,default='1'); created=Column(DateTime,default=datetime.datetime.utcnow)
class Slide(Base):
 __tablename__='slides'
 id=Column(String,primary_key=True); post_id=Column(String,ForeignKey('posts.id')); position=Column(String); headline=Column(Text); body=Column(Text)
class PublishAttempt(Base):
 __tablename__="publish_attempts"
 id=Column(String,primary_key=True);post_id=Column(String,nullable=False);version=Column(String,nullable=False);status=Column(String,nullable=False);external_id=Column(String);error=Column(Text);created=Column(DateTime,default=datetime.datetime.utcnow)
class Audit(Base):
 __tablename__='audit'
 id=Column(String,primary_key=True); post_id=Column(String); event=Column(String); created=Column(DateTime,default=datetime.datetime.utcnow)
from daily import register_source_model, ingest
from source_urls import canonical_source_url
SourceCandidate = register_source_model(Base)
Base.metadata.create_all(engine)
app=FastAPI(title='DevAI Studio API')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','),allow_methods=['*'],allow_headers=['*'])
class PostInput(BaseModel):
 title:str; caption:str=''; slides:list[dict]=[]
class UpdateInput(BaseModel):
 title:Optional[str]=None; caption:Optional[str]=None

def auth(x_api_key:Optional[str]):
 key=os.getenv('ADMIN_API_KEY','local-dev-only')
 if x_api_key!=key: raise HTTPException(401,'Unauthorized')
def serialize(db,p):
 return dict(id=p.id,title=p.title,caption=p.caption,status=p.status,version=p.version,created=p.created.isoformat(),slides=[dict(id=s.id,headline=s.headline,body=s.body,position=int(s.position)) for s in db.query(Slide).filter_by(post_id=p.id).order_by(Slide.position).all()])
@app.get('/health')
def health():return {'status':'ok'}
@app.get('/posts')
def posts(x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session() as db:return [serialize(db,p) for p in db.query(Post).order_by(Post.created.desc()).all()]
@app.post('/posts')
def create(data:PostInput,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session.begin() as db:
  p=Post(id=str(uuid.uuid4()),title=data.title,caption=data.caption);db.add(p)
  for i,s in enumerate(data.slides):db.add(Slide(id=str(uuid.uuid4()),post_id=p.id,position=str(i+1).zfill(3),headline=s.get('headline',''),body=s.get('body','')))
  db.add(Audit(id=str(uuid.uuid4()),post_id=p.id,event='created'))
  return {'id':p.id}
@app.patch('/posts/{id}')
def update(id:str,data:UpdateInput,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session.begin() as db:
  p=db.get(Post,id)
  if not p:raise HTTPException(404)
  if p.status in ('publishing','published'):raise HTTPException(409,'Cannot edit publishing/published content')
  if data.title is not None:p.title=data.title
  if data.caption is not None:p.caption=data.caption
  p.version=str(int(p.version)+1);p.status='draft';db.add(Audit(id=str(uuid.uuid4()),post_id=id,event='edited; approval invalidated'))
  return {'status':p.status,'version':p.version}
@app.post('/posts/{id}/{action}')
def transition(id:str,action:str,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 allowed={'submit':({'draft','rejected'},'pending_review'),'approve':({'pending_review'},'approved'),'reject':({'pending_review'},'rejected')}
 if action=='publish':
  with Session() as db:
   p=db.get(Post,id)
   if not p:raise HTTPException(404)
   if p.status!='approved':raise HTTPException(409,'Post requires approval before publishing')
  raise HTTPException(503,'Publishing requires configured Instagram credentials and explicit public media URLs')
 if action not in allowed:raise HTTPException(400,'Unknown transition')
 with Session.begin() as db:
  p=db.get(Post,id)
  if not p:raise HTTPException(404)
  from_states,target=allowed[action]
  if p.status not in from_states:raise HTTPException(409,'Invalid status transition')
  p.status=target;db.add(Audit(id=str(uuid.uuid4()),post_id=id,event=f'{action} version {p.version}'))
  return {'status':p.status}
@app.get('/posts/{id}/audit')
def audit(id:str,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session() as db:return [{'event':a.event,'created':a.created.isoformat()} for a in db.query(Audit).filter_by(post_id=id).order_by(Audit.created).all()]

from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile

class SlideUpdate(BaseModel):
 headline: Optional[str]=None
 body: Optional[str]=None

def draw_slide(headline, body, index, total):
 im=Image.new('RGB',(1080,1350),(13,17,34))
 d=ImageDraw.Draw(im)
 d.ellipse((450,100,1450,1100),fill=(35,28,82))
 d.rounded_rectangle((66,70,1014,1280),radius=36,outline=(88,82,144),width=3)
 bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
 regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 title_font=ImageFont.truetype(bold,66)
 body_font=ImageFont.truetype(regular,35)
 label_font=ImageFont.truetype(bold,24)
 d.text((115,133),'DEVAISTUDIO  /  ENGINEERING NOTES',font=label_font,fill=(124,216,247))
 def lines(text,font,width):
  result=[]; current=''
  for word in text.split():
   candidate=(current+' '+word).strip()
   if d.textbbox((0,0),candidate,font=font)[2]>width and current:
    result.append(current);current=word
   else:current=candidate
  if current:result.append(current)
  return result
 y=400
 for line in lines(headline,title_font,820)[:5]:
  d.text((115,y),line,font=title_font,fill='white');y+=87
 y+=45
 for line in lines(body,body_font,815)[:9]:
  d.text((115,y),line,font=body_font,fill=(198,205,228));y+=54
 d.line((115,1170,960,1170),fill=(94,96,157),width=3)
 d.text((115,1200),'BUILD SMARTER. SHIP BETTER.',font=label_font,fill=(147,153,205))
 d.text((875,1200),f'{index:02d} / {total:02d}',font=label_font,fill=(147,216,247))
 output=BytesIO();im.save(output,format='PNG',optimize=True);return output.getvalue()

@app.patch('/posts/{id}/slides/{slide_id}')
def update_slide(id:str,slide_id:str,data:SlideUpdate,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session.begin() as db:
  p=db.get(Post,id)
  if not p:raise HTTPException(404,'Post not found')
  if p.status in ('publishing','published'):raise HTTPException(409,'Post cannot be edited')
  s=db.get(Slide,slide_id)
  if not s or s.post_id!=id:raise HTTPException(404,'Slide not found')
  if data.headline is not None:s.headline=data.headline
  if data.body is not None:s.body=data.body
  p.version=str(int(p.version)+1);p.status='draft'
  db.add(Audit(id=str(uuid.uuid4()),post_id=id,event=f'slide edited; approval invalidated; version {p.version}'))
  return {'status':p.status,'version':p.version}

@app.get('/posts/{id}/slides/{slide_id}/image')
def slide_image(id:str,slide_id:str,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session() as db:
  p=db.get(Post,id)
  s=db.get(Slide,slide_id)
  if not p or not s or s.post_id!=id:raise HTTPException(404)
  slides=db.query(Slide).filter_by(post_id=id).order_by(Slide.position).all()
  return Response(draw_slide(s.headline or '',s.body or '',next(i for i,v in enumerate(slides,1) if v.id==slide_id),len(slides)),media_type='image/png')

@app.get('/posts/{id}/export')
def export_post(id:str,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 with Session() as db:
  p=db.get(Post,id)
  if not p:raise HTTPException(404)
  slides=db.query(Slide).filter_by(post_id=id).order_by(Slide.position).all()
  if not slides:raise HTTPException(409,'No slides to export')
  stream=BytesIO()
  with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
   for i,s in enumerate(slides,1):z.writestr(f'slide_{i:02d}.png',draw_slide(s.headline or '',s.body or '',i,len(slides)))
   z.writestr('caption.txt',p.caption or '')
  return Response(stream.getvalue(),media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="devai-{id}.zip"'})

from research import discover, create_editorial_draft

@app.get('/research/discover')
def research_discover(x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 return discover()

class ResearchDraftInput(BaseModel):
 title:str
 url:str
 source:str='Primary source'

@app.post('/research/draft')
def research_draft(data:ResearchDraftInput,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 try: source_url=canonical_source_url(data.url)
 except ValueError as exc: raise HTTPException(422,str(exc))
 payload=create_editorial_draft({**data.model_dump(),'url':source_url})
 with Session.begin() as db:
  p=Post(id=str(uuid.uuid4()),title=payload['title'],caption=payload['caption']);db.add(p)
  for i,s in enumerate(payload['slides'],1):
   db.add(Slide(id=str(uuid.uuid4()),post_id=p.id,position=f'{i:03d}',headline=s['headline'],body=s['body']))
  db.add(Audit(id=str(uuid.uuid4()),post_id=p.id,event=f'research draft from {data.url}; unverified scaffold'))
  return {'id':p.id,'status':'draft','verification_required':True}

class PublishInput(BaseModel):
 image_urls:list[str]

@app.post('/posts/{id}/publish')
def publish_approved(id:str,data:PublishInput,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 if not os.getenv('INSTAGRAM_ACCESS_TOKEN') or not os.getenv('INSTAGRAM_ACCOUNT_ID'):
  raise HTTPException(503,'Instagram credentials not configured')
 if not 2<=len(data.image_urls)<=10 or any(not url.startswith('https://') for url in data.image_urls):
  raise HTTPException(422,'Provide 2–10 publicly accessible HTTPS JPEG image URLs')
 with Session.begin() as db:
  p=db.get(Post,id)
  if not p:raise HTTPException(404)
  if p.status!='approved':raise HTTPException(409,'Only approved content can be published')
  slides=db.query(Slide).filter_by(post_id=id).all()
  if len(slides)!=len(data.image_urls):raise HTTPException(422,'Image count must match approved slide count')
  attempt_id=str(uuid.uuid4());version=p.version;caption=p.caption
  p.status='publishing'
  db.add(PublishAttempt(id=attempt_id,post_id=id,version=version,status='started'))
  db.add(Audit(id=str(uuid.uuid4()),post_id=id,event=f'publishing reserved version {version}'))
 try:
  from instagram import InstagramPublisher
  external_id=InstagramPublisher().publish_carousel(data.image_urls,caption)
 except Exception as exc:
  with Session.begin() as db:
   attempt=db.get(PublishAttempt,attempt_id);attempt.status='needs_reconciliation';attempt.error=str(exc)[:1000]
   db.add(Audit(id=str(uuid.uuid4()),post_id=id,event='publish failed or uncertain; manual reconciliation required'))
  raise HTTPException(502,'Instagram publish failed or outcome uncertain. Reconcile manually; automatic retry disabled')
 with Session.begin() as db:
  p=db.get(Post,id);p.status='published'
  attempt=db.get(PublishAttempt,attempt_id);attempt.status='published';attempt.external_id=external_id
  db.add(Audit(id=str(uuid.uuid4()),post_id=id,event=f'published version {version}, media {external_id}'))
 return {'status':'published','instagram_media_id':external_id}

from generation import generate
from difflib import SequenceMatcher

class GenerateInput(BaseModel):
 title:str
 url:str
 excerpt:str

@app.post('/research/generate')
def generate_post(data:GenerateInput,x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 try: source_url=canonical_source_url(data.url)
 except ValueError as exc: raise HTTPException(422,str(exc))
 if len(data.excerpt.strip())<120:
  raise HTTPException(422,'Source excerpt of at least 120 characters required')
 with Session() as db:
  titles=[p.title for p in db.query(Post).all()]
  if any(SequenceMatcher(None,data.title.casefold(),title.casefold()).ratio()>=0.86 for title in titles):
   raise HTTPException(409,'Similar post title already exists; review existing content first')
 try:
  generated=generate(data.title,source_url,data.excerpt)
 except (ValueError,RuntimeError) as exc:
  raise HTTPException(422,str(exc))
 except Exception:
  raise HTTPException(502,'AI generation failed; no draft was saved')
 with Session.begin() as db:
  p=Post(id=str(uuid.uuid4()),title=generated['title'],caption=generated['caption']);db.add(p)
  for i,s in enumerate(generated['slides'],1):
   db.add(Slide(id=str(uuid.uuid4()),post_id=p.id,position=f'{i:03d}',headline=s['headline'],body=s['body']))
  db.add(Audit(id=str(uuid.uuid4()),post_id=p.id,event=f'AI-generated draft from {source_url}; fact-check required'))
  return {'id':p.id,'status':'draft','fact_check_required':True}

@app.post('/research/ingest')
def ingest_daily(x_api_key:Optional[str]=Header(None)):
 auth(x_api_key)
 return ingest(Session, SourceCandidate, Post, Slide, Audit)
