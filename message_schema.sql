CREATE TABLE messages(msg_id varchar(16) PRIMARY KEY, data TEXT, listeners INTEGER, topic_id INTEGER);
CREATE TABLE subscriber(name TEXT PRIMARY KEY, topic_id INTEGER, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP , msg_id varchar(16));
CREATE TABLE topics (topic_id integer PRIMARY KEY AUTOINCREMENT,  name TEXT);  
