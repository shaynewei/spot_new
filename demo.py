#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import Flask
from gevent import pywsgi

app = Flask(__name__)

@app.route('/metrics')
def hello():
 return 'metrics'

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
