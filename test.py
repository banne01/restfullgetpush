import pycurl
import urllib
import string
import random
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

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
        code = c.getinfo(c.RESPONSE_CODE)
        c.close()
        return code 
    def testSubscribe (self, topic, subs):
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, "")
        c.perform()
        print('Status: %d' % c.getinfo(c.RESPONSE_CODE))
        code = c.getinfo(c.RESPONSE_CODE)
        c.close()
        return code 

    def testGet (self, topic, subs):
        buffer = BytesIO()
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        #c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.WRITEFUNCTION, buffer.write)
        print c.perform()
        print('Status: %d' % c.getinfo(c.RESPONSE_CODE))
        body = buffer.getvalue()
        c.close()
        return body
    
    def testUnSubscribe (self, topic, subs):
        url = test_url + "/" + topic + "/" + subs
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        c.perform()
        code = c.getinfo(c.RESPONSE_CODE)
        c.close()
        return code 

def str_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def test4():
    msg = {}
    sub1 = str_generator(size=6)
    sub2 = str_generator(size=6)
    test.testSubscribe(topics[0], sub1) 
    test.testSubscribe(topics[0], sub2) 
    for i in range(1,10):
        msg[i] = str_generator(size=20)
        test.testPost(topics[0], msg[i])
    for i in range(1,10):
        rt = test.testGet(topics[0],sub1)
        assert msg[i] == rt
        rt = test.testGet(topics[0],sub2)
        assert msg[i] == rt
    test.testUnSubscribe(topics[0], sub1) 
    test.testUnSubscribe(topics[0], sub2) 


## test get before put
def test3():
    for i in [0]:
        st = str_generator(size=10)
        sub1 = str_generator(size=6)
        test.testSubscribe(topics[0], sub1) 
        rt = test.testGet(topics[i],sub1)
        if rt:
            assert(True)
        test.testPost(topics[i], st)
        rt = test.testGet(topics[i],sub1)
        assert (st==rt)
        test.testUnSubscribe(topics[i], sub1) 
## test seq mesaages
def test2():
    msg = {}
    sub1 = str_generator(size=6)
    test.testSubscribe(topics[0], sub1) 
    for i in range(1,10):
        msg[i] = str_generator(size=20)
        test.testPost(topics[0], msg[i])
    for i in range(1,10):
        rt = test.testGet(topics[0],sub1)
        assert msg[i] == rt
    test.testUnSubscribe(topics[0], sub1) 

## test all topics
def test1():
    for i in [0, 1 ,2]:
        st = str_generator(size=10)
        sub1 = str_generator(size=6)
        test.testSubscribe(topics[i], sub1) 
        test.testPost(topics[i], st)
        rt = test.testGet(topics[i],sub1)
        assert (st==rt)
        test.testUnSubscribe(topics[i], sub1) 


if __name__=='__main__':

    test = testRest()
    #test1()
    #test2()
    #test3()
    test4()
