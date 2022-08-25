#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import Flask
app = Flask(__name__)

@app.route('/metrics')
def hello():
 return 'metrics'

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)