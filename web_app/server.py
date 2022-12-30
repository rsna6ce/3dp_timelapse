#!/usr/bin/env python3
#coding:utf-8

from web_ui import app
from web_ui import config

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.FLASK_PORT, threaded=True)
