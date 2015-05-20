from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
try:
    import cPickle as pickle
except:
    import pickle
import pprint
import threading
import re
import cgi
import os
import redis
import pika

topics = ['sports', 'politics', 'religion']

# subscriptiob database in memory
# can be ported to redis type backend
class SubscrptiobDB():
    def __init__(self):
        self.subDict  = dict()
    
    #insert into a topic subs
    def insertSub(self, subs, topic, queue):
        if subs in self.subDict.keys():
            topic_dict = self.subDict[subs]
            topic_dict[topic] = queue
        else:
            topic_dict = dict();
            topic_dict[topic] = queue;
            self.subDict[subs] = topic_dict
    
    def deleteSub(self, sub, topic):
        if sub in self.subDict.keys():
            topic_dict = self.subDict[sub]
            del topic_dict[topic]
    
    def getSub(self, subs, topic):
        if subs in self.subDict.keys():
            topic_dict = self.subDict[subs]
            if topic in topic_dict.keys():
                return topic_dict[topic]
            else:
                return None
        else:
            return None

    def _debug(self):
        print self.subDict
    
class RabbitQ():
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        self.channel = self.connection.channel()
        self.createTopicExchange()
        #kesy for dictionary
        self.subDict  =  SubscrptiobDB()

    #close connection and delete queues
    def __del__(self):
        self.connection.close()
    
    def createTopicExchange(self):
    #create a exchange for each of the topics
        for t in topics:
            self.channel.exchange_declare(exchange=t,
                         type='fanout')
    
    def publisToTopic(self, t, message):
        #publis to topic
        if self.checktopic(t):
            self.channel.basic_publish(exchange= t,
                     routing_key='', body=message)
    
    def subscribeTopic(self, t, consumer):
        #create a new queue and output it to a map 
        if self.checktopic(t) == False:
            return   
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        print queue_name
        self.channel.queue_bind(exchange=t, queue=queue_name)
        self.subDict.insertSub(consumer, t, queue_name)
        print self.subDict._debug()
    
    def unSubscrubetoTopic(self, t, consumer):
        self.subDict.deleteSub(consumer, t) 
        print self.subDict._debug()
         

    def callback(self, ch, method, properties, body):
        print " [x] %r" % (body,)
    
    def recvMessageonTopic(self, t, consumer, HttpCallback):
        queue_name = self.subDict.getSub(consumer, t) 
        if queue_name is None:
            return
        self.channel.basic_consume(self.callback,
                      queue=queue_name,
                      no_ack=True)

    def checktopic(self, t):   
        for t in topics:
            if t in topics:
                return True
        return False
    
class HTTPRequestHandler(BaseHTTPRequestHandler):
    
    def pathsplit(self, path):
        #rest_path = []
        path_list = path.split('/')
        while '' in path_list:
            path_list.remove('')
        return path_list
    
    def sendResp(self, respcode):
        self.send_response(respcode)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

    def do_POST(self):
        split = self.pathsplit(self.path)
        #print "request path %s"%self.path
        print split  
        if len(split) > 2:
            self.sendResp(400)
            return
        if len(split) == 1:
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            if ctype != 'application/x-www-form-urlencoded':
                self.sendResp(400)
                return
            length = int(self.headers['content-length'])
            postvars = cgi.parse_qs(
                        self.rfile.read(length), 
                        keep_blank_values=1)
            #print "post lenght %d"% length
            print postvars
            topic = split[0] 
            q = RabbitQ()
            q.publisToTopic(topic, postvars['data'][0])
        else:   
            topic = split[0]    
            subcr = split[1]
            q = RabbitQ()
            q.subscribeTopic(topic, subcr)
        self.sendResp(200)

    def do_GET(self):
       # if None != re.search('/api/v1/getrecord/*', self.path):
       #     recordID = self.path.split('/')[-1]
       #     if LocalData.records.has_key(recordID):
       #         self.send_response(200)
       #         self.send_header('Content-Type', 'text/plain')
       #         self.end_headers()
       #         self.wfile.write(LocalData.records[recordID])
       #     else:
       #         self.send_response(400, 'Bad Request: record does not exist')
       #         self.send_header('Content-Type', 'application/json')
       #         self.end_headers()
       # else:
       #     self.send_response(403)
       #     self.send_header('Content-Type', 'application/json')
       #     self.end_headers()
        print self.path
        split = self.pathsplit(self.path)
        #print "request path %s"%self.path
        print split 
        if len(split) != 2:
            self.sendError(400)
        topic = split[0]    
        subcr = split[1]
          
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
    
    #def do_PUT(self):
    #    print self.path
    #    split = self.pathsplit(self.path)
    #    print "request path %s"%self.path
    #    print split 
    #    self.send_response(200)
    #    self.send_header('Content-Type', 'text/plain')
    #    self.end_headers()
    
    def do_DELETE(self):
        split = self.pathsplit(self.path)
        print split 
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

 
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
 
    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)
 
class SimpleHttpServer():
    def __init__(self, ip, port):
        self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)
 
    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = False
        self.server_thread.start()
 
    def waitForThread(self):
        self.server_thread.join()
 
    def stop(self):
        self.server.shutdown()
        self.waitForThread()
 
if __name__=='__main__':
    #parser = argparse.ArgumentParser(description='HTTP Server')
    #parser.add_argument('port', type=int, help='Listening port for HTTP Server')
    #parser.add_argument('ip', help='HTTP Server IP')
    #args = parser.parse_args()
    #server = SimpleHttpServer(args.ip, args.port)
    server = SimpleHttpServer("127.0.0.1", 8080)
    print 'HTTP Server Running...........'
    mq = RabbitQ()
    
    #mq.subscribeTopic(topics[0],"one")
    #mq.subscribeTopic(topics[1],"one")
    
    
    #mq.publisToTopic(topics[1], "time2")
    #mq.recvMessageonTopic(topics[0], "one", None)
    #mq.recvMessageonTopic(topics[1], "one")
    #mq.publisToTopic(topics[0], "time1")
    #mq.recvMessageonTopic(topics[0], "one")
    #mq.unSubscrubetoTopic(topics[0],"one")
    #mq.unSubscrubetoTopic(topics[1],"one")

    server.start()
    server.waitForThread()
 
