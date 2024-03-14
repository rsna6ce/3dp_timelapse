from flask import Flask
import logging
import json
import os


from web_ui import config
if not config.DEBUG:
    # Mask Flask log output, if Not in DEBUG mode.
    logger = logging.getLogger()
    logger.addHandler(logging.FileHandler("/dev/null"))

app = Flask(__name__)
app.config.from_object('web_ui.config')

web_ui_path = os.path.dirname(os.path.abspath(__file__))
param_json = web_ui_path + '/param.json'
with open(param_json, mode = 'r', encoding = 'utf-8') as f:
    param = json.load(f)
app.config["web_ui_path"] = web_ui_path

from web_ui.models import status
inner_status = status.Status()

from web_ui.camera import camera

from web_ui.views import views
from web_ui.views import capture
from web_ui.views import video
from web_ui.views import settings

