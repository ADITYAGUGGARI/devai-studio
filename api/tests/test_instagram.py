from instagram import InstagramPublisher, PublishError
import pytest

class Response:
 def __init__(self,body):self.body=body
 def raise_for_status(self):pass
 def json(self):return self.body
class Client:
 def __init__(self):self.calls=[];self.count=0
 def post(self,url,data):
  self.calls.append(('POST',url,data));self.count+=1
  return Response({'id':f'container-{self.count}'})
 def get(self,url,params):
  self.calls.append(('GET',url,params));return Response({'status_code':'FINISHED'})

def test_carousel_sequence():
 c=Client();p=InstagramPublisher(token='test',account_id='123',client=c)
 assert p.publish_carousel(['https://example.com/a.jpg','https://example.com/b.jpg'],'caption')=='container-4'
 assert len([x for x in c.calls if x[0]=='POST'])==4
 assert c.calls[-1][1].endswith('/123/media_publish')
 assert c.calls[-1][2]['creation_id']=='container-3'

def test_invalid_images_rejected_before_network():
 c=Client();p=InstagramPublisher(token='test',account_id='123',client=c)
 with pytest.raises(PublishError):p.publish_carousel(['http://example.com/a.jpg','https://example.com/b.jpg'],'x')
 assert c.calls==[]
