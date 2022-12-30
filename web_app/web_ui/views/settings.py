from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import inner_status

@app.route('/settings')
def settings():
    return render_template(
        'menu.html', navi_title="settings")