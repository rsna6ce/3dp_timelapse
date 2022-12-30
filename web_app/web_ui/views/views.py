from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import inner_status

@app.errorhandler(404)
def non_existant_route(error):
   return redirect(url_for('menu'))

@app.route('/menu')
def menu():
    return render_template(
        'menu.html', navi_title="menu")