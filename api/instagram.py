"""Meta carousel publishing adapter. No automatic retries of the final publish call."""
import os, time
import httpx

class PublishError(RuntimeError): pass

class InstagramPublisher:
    def __init__(self, token=None, account_id=None, version=None, client=None):
        self.token=token or os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.account_id=account_id or os.getenv('INSTAGRAM_ACCOUNT_ID')
        self.version=version or os.getenv('META_GRAPH_VERSION','v24.0')
        self.client=client or httpx.Client(timeout=30)
        if not self.token or not self.account_id: raise PublishError('Instagram credentials not configured')
        if not self.version.startswith('v') or not self.version[1:].replace('.','').isdigit(): raise PublishError('Invalid Graph API version')
        self.base=f'https://graph.facebook.com/{self.version}'
    def post(self, path, data):
        r=self.client.post(f'{self.base}/{path}',data={**data,'access_token':self.token})
        r.raise_for_status(); body=r.json()
        if not body.get('id'):raise PublishError('Meta returned no media container ID')
        return body['id']
    def wait_ready(self, container, attempts=12):
        for i in range(attempts):
            r=self.client.get(f'{self.base}/{container}',params={'fields':'status_code','access_token':self.token})
            r.raise_for_status(); status=r.json().get('status_code')
            if status=='FINISHED':return
            if status in ('ERROR','EXPIRED'):raise PublishError(f'Container {container}: {status}')
            if i<attempts-1:time.sleep(2)
        raise PublishError('Media processing timed out; do not retry publish automatically')
    def publish_carousel(self, image_urls, caption):
        if not 2<=len(image_urls)<=10:raise PublishError('Carousel requires 2–10 images')
        if any(not u.startswith('https://') for u in image_urls):raise PublishError('Public HTTPS image URLs required')
        children=[]
        for url in image_urls:
            child=self.post(f'{self.account_id}/media',{'image_url':url,'is_carousel_item':'true'})
            self.wait_ready(child)
            children.append(child)
        parent=self.post(f'{self.account_id}/media',{'media_type':'CAROUSEL','children':','.join(children),'caption':caption})
        self.wait_ready(parent)
        return self.post(f'{self.account_id}/media_publish',{'creation_id':parent})
