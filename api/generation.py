"""Grounded AI editorial generation. Never treats model output as verified facts."""
import json
import os
import httpx

SYSTEM = """You are a meticulous software-engineering editor. Use ONLY the supplied source excerpt as evidence for factual claims. Never invent dates, numbers, performance claims, quotations, or API capabilities. Explain technical implications as analysis, clearly distinguishing them from source claims. Return only JSON with keys title (string), caption (string), slides (array of exactly 8 objects with headline and body strings). Slides must be concise and educational. End caption with the exact supplied source URL. Do not reuse source text verbatim except proper nouns. No markdown fences."""

def validate_generated(data, source_url):
    if not isinstance(data, dict) or not all(k in data for k in ('title','caption','slides')):
        raise ValueError('Missing generated content')
    if not isinstance(data['slides'], list) or len(data['slides']) != 8:
        raise ValueError('Exactly eight slides required')
    if not isinstance(data['title'], str) or not 5 <= len(data['title']) <= 160:
        raise ValueError('Invalid title')
    if not isinstance(data['caption'], str) or source_url not in data['caption']:
        raise ValueError('Caption must cite source')
    for slide in data['slides']:
        if not isinstance(slide,dict) or not isinstance(slide.get('headline'),str) or not isinstance(slide.get('body'),str):
            raise ValueError('Invalid slide')
        if not 3 <= len(slide['headline']) <= 130 or not 5 <= len(slide['body']) <= 650:
            raise ValueError('Slide exceeds content limits')
    return data

def generate(source_title, source_url, source_excerpt, model=None):
    if len(source_excerpt.strip()) < 120:
        raise ValueError('Source excerpt too short for grounded generation')
    api_key=os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not configured')
    model=model or os.getenv('OPENAI_MODEL','gpt-4.1-mini')
    response=httpx.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {api_key}'},json={
        'model':model,'temperature':0.3,'response_format':{'type':'json_object'},
        'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'source_title':source_title,'source_url':source_url,'source_excerpt':source_excerpt[:16000]})}]
    },timeout=90)
    response.raise_for_status()
    content=response.json()['choices'][0]['message']['content']
    return validate_generated(json.loads(content),source_url)
