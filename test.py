import pycurl
import urllib
test_url = "http://localhost:8080"
topics = ['sports', 'politics', 'religion']

class testRest():

    def __init__(self):
        pass
    def testPost(self, topic, data):
        url = test_url + "/" + topic
        print url
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 1)
        var = dict()
        var['data'] = data
        post = urllib.urlencode(var)
        c.setopt(pycurl.POSTFIELDS, post)
        c.perform()
        c.close()
        
    def testSubscribe (self, topic, subs):
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, "")
        c.perform()
        c.close()
    
    def testGet (self, topic, subs):
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        #c.setopt(pycurl.GET, 1)
        #c.setopt(pycurl.GETFIELDS, "")
        c.perform()
        c.close()
    
    def testUnSubscribe (self, topic, subs):
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, test_url)
        c.setopt(pycurl.DELETE, 1)
        c.setopt(pycurl.DELETEFIELDS, "")
        c.perform()
        c.close()

if __name__=='__main__':

    test = testRest()
    print test
    sub1 = "sub1"
    test.testSubscribe(topics[0], sub1) 
    test.testPost(topics[0], "Who won ?")
    test.testGet(topics[0],sub1)
