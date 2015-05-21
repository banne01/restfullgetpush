from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import pprint
import threading
import cgi
import os
import pika
import sys

# list of topics ..keep is simple
topics = ['sports', 'politics', 'religion']
debug_mode = False
# there are better ways for signleton then static variable
# Need to to make RabbitMQ singleton later
RabbitQ_singleton = None
# subscriptiob database in memory
# can be ported to redis type backend for extention
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
    # delte subscription 
    def deleteSub(self, sub, topic):
        if sub in self.subDict.keys():
            topic_dict = self.subDict[sub]
            del topic_dict[topic]
            ##purge empty kesy 
            if bool(topic_dict) is False:
                self.subDict.pop(sub, None)  
    # get subscription 
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
#This class handle all messaging queues
#There is a exchange per topic and queue per subscriber to the topic
#
class RabbitQ():
    def __init__(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        except:
            raise
        self.channel = self.connection.channel()
        self.createTopicExchange()
        #subscriptionDB
        self.subDict  =  SubscrptiobDB()

    #close connection and delete queues
    def __del__(self):
        self.connection.close()
        for t in topics:
            self.channel.exchange_delete(exchange=t)
            self.channel.close() 
    def createTopicExchange(self):
    #create a exchange for each of the topics
        for t in topics:
            self.channel.exchange_declare(exchange=t,
                         type='fanout')
    
    def publisToTopic(self, t, message):
        #publish to topic
        if self.checktopic(t):
            self.channel.basic_publish(exchange= t,
                     routing_key='', body=message)
    
    def subscribeTopic(self, t, consumer):
        #create a new queue and output it to a map 
        if self.checktopic(t) == False:
            return   
        result = self.channel.queue_declare(exclusive=True,auto_delete=True)
        queue_name = result.method.queue
        if debug_mode:
            print queue_name
        self.channel.queue_bind(exchange=t, queue=queue_name)
        self.subDict.insertSub(consumer, t, queue_name)
        if debug_mode:
            print self.subDict._debug()
    
    def unSubscrubetoTopic(self, t, consumer):
        queue_name = self.subDict.getSub(consumer, t) 
        if queue_name is None:
            return 400
        self.channel.queue_delete(queue=queue_name)
        self.subDict.deleteSub(consumer, t) 
        if debug_mode:
            print self.subDict._debug()
        return 200
         
    def recvMessageonTopic(self, t, consumer):
        if debug_mode:
            print " revMesg on topic"
            print self.subDict._debug()
        queue_name = self.subDict.getSub(consumer, t) 
        if queue_name is None:
            return 404,None
        method_frame, header_frame, body = self.channel.basic_get(queue_name, False)
        if method_frame:
            if debug_mode:
                print method_frame, header_frame, body
            return 200, body
                
        else:
            return 400,None

    def checktopic(self, t):   
        for t in topics:
            if t in topics:
                return True
        return False


class HTTPRequestHandler(BaseHTTPRequestHandler):
    
    def pathsplit(self, path):
        path_list = path.split('/')
        while '' in path_list:
            path_list.remove('')
        return path_list
    
    def sendResp(self, respcode):
        self.send_response(respcode)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

    def do_POST(self):
        if debug_mode:
            print "Post request"
        split = self.pathsplit(self.path)
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
            if debug_mode:
                print postvars
            topic = split[0] 
            RabbitQ_singleton.publisToTopic(topic, postvars['data'][0])
        else:   
            topic = split[0]    
            subcr = split[1]
            RabbitQ_singleton.subscribeTopic(topic, subcr)
        self.sendResp(200)

    def do_GET(self):
        if debug_mode:
            print "Get request"
            print self.path
        split = self.pathsplit(self.path)
        if len(split) != 2:
            self.sendResp(400)
        topic = split[0]    
        subcr = split[1]
        code, msg = RabbitQ_singleton.recvMessageonTopic(topic, subcr)
        if debug_mode:
            print code, msg
        if code != 200:
            self.sendResp(code)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(msg)
    
    def do_DELETE(self):
        if debug_mode:
            print "Delete request"
            print self.path
        split = self.pathsplit(self.path)
        if len(split) != 2:
            self.sendResp(400)
            return
        topic = split[0]    
        subcr = split[1]
        code = RabbitQ_singleton.unSubscrubetoTopic(topic, subcr)
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

#create a threaded http server
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
    #args = parser.parse_args()
    #server = SimpleHttpServer(args.ip, args.port)
    print "Straring RabbitQ connections.."
    try:
        RabbitQ_singleton = RabbitQ()
    except Exception, e:
        print "Can not connect to RabbitQ server "
        print "Run RabbitMQ server before staring server by following"
        print "\t ./rabbitmq-server"
        sys.exit(1)
    print 'HTTP Server Running...........'
    server = SimpleHttpServer("127.0.0.1", 8080)
    server.start()
    server.waitForThread()
 
