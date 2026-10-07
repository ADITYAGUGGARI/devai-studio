"""Source-backed draft discovery. No invented announcements when feeds are unavailable."""
import re
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = {
    'GitHub Blog': 'https://github.blog/feed/',
    'Google Developers': 'https://developers.googleblog.com/feeds/posts/default',
}

def fetch_feed(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': 'DevAIStudio/0.3 (+source-attribution)'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = response.read(1_000_000)
    root = ET.fromstring(data)
    items=[]
    for item in root.findall('.//item')[:20]:
        title=item.findtext('title') or ''
        link=item.findtext('link') or ''
        if title and link.startswith('https://'):
            items.append({'title':title.strip(),'url':link,'published':item.findtext('pubDate') or ''})
    ns={'a':'http://www.w3.org/2005/Atom'}
    for entry in root.findall('a:entry',ns)[:20]:
        title=entry.findtext('a:title',default='',namespaces=ns)
        link=next((e.attrib.get('href','') for e in entry.findall('a:link',ns) if e.attrib.get('rel','alternate')=='alternate'), '')
        if title and link.startswith('https://'):
            items.append({'title':title.strip(),'url':link,'published':entry.findtext('a:updated',default='',namespaces=ns)})
    return items

def discover(feeds=None):
    results=[]; errors=[]
    for name,url in (feeds or FEEDS).items():
        try:
            for item in fetch_feed(url):
                item['source']=name
                results.append(item)
        except Exception as exc:
            errors.append(f'{name}: {type(exc).__name__}')
    pattern=re.compile(r'\b(ai|agent|llm|model|copilot|code|coding|developer|software|machine learning|security|python|api)\b',re.I)
    return {'articles':[a for a in results if pattern.search(a['title'])][:30], 'errors':errors}

def create_editorial_draft(article):
    """Explicitly non-factual editorial scaffold until a human verifies source."""
    title=article['title'][:160]
    slides=[
        {'headline':title,'body':'A developer-focused story to investigate. Source linked in caption.'},
        {'headline':'WHAT WAS ANNOUNCED?','body':'Read the primary source and summarize its confirmed claims before approval.'},
        {'headline':'WHY DEVELOPERS CARE','body':'Evaluate the impact on developer workflow, reliability, and maintainability.'},
        {'headline':'HOW DOES IT WORK?','body':'Add an accurate technical diagram or verified implementation example.'},
        {'headline':'PRODUCTION CHECKLIST','body':'Assess latency, cost, security, observability, and fallback behavior.'},
        {'headline':'WHAT TO TEST','body':'Benchmark on your own workloads; measure quality and regressions.'},
        {'headline':'TRADE-OFFS','body':'Identify limitations, prerequisites, and unsupported use cases.'},
        {'headline':'YOUR TAKEAWAY','body':'Add a verified actionable conclusion before publication.'},
    ]
    return {'title':title,'caption':f'Developer news to verify: {title}\n\nPrimary source: {article["url"]}\n\n#AIEngineering #SoftwareDevelopment', 'slides':slides}
