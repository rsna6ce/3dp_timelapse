import os
import sys
from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import config
from web_ui import inner_status
import socket

@app.route('/settings')
def settings():
    return render_template(
        'settings.html', navi_title="settings")

@app.route('/reset/server', methods=['POST'])
def reset_server():
    print("os._exit(0)")
    os._exit(0)

@app.route('/shutdown/pc', methods=['POST'])
def shutdown_pc():
    udp_shutdown_sh_address = ('127.0.0.1', config.SHUTDOWN_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_len = sock.sendto('shutdown now'.encode('utf-8'), udp_shutdown_sh_address)
    os._exit(0)
