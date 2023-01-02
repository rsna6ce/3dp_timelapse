import os
import sys
from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import inner_status

@app.route('/settings')
def settings():
    return render_template(
        'settings.html', navi_title="settings")

@app.route('/reset/server', methods=['POST'])
def reset_server():
    print("os._exit(0)")
    os._exit(0)

