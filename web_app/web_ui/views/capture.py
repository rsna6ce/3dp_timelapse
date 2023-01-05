import os
import time
import threading
import cv2
import numpy as np
from datetime import datetime, timedelta
from flask import request, redirect, url_for, render_template, flash, jsonify, Response
from web_ui import app
from web_ui import inner_status
from web_ui import camera
from web_ui import param
from web_ui import web_ui_path

@app.route('/capture')
def capture():
    start_enable = 'disabled' if inner_status.capture_running else ''
    stop_enable = '' if inner_status.capture_running else 'disabled'
    autostop_no_motion_enable = 'checked' if inner_status.capture_autostop_no_motion else ''
    if not inner_status.capture_running:
        inner_status.capture_interval_sec = param['capture_default_interval_sec']
        inner_status.capture_autostop_timer_sec = 0
        inner_status.capture_autostop_no_motion = True
        inner_status.capture_count = 0
    return render_template(
        'capture.html', navi_title="capture",
        capture_running=inner_status.capture_running,
        start_enable=start_enable, stop_enable=stop_enable,
        autostop_timer_hour = int(inner_status.capture_autostop_timer_sec / 3600),
        autostop_timer_minute = int((inner_status.capture_autostop_timer_sec % 3600) / 60),
        capture_interval_sec = inner_status.capture_interval_sec,
        autostop_no_motion_enable = autostop_no_motion_enable)

@app.route('/capture/status')
def capture_status():
    return jsonify({
        'capture_running' : inner_status.capture_running,
        'capture_started_datetime' : inner_status.capture_started_datetime.strftime('%Y/%m/%d-%H:%M:%S') if inner_status.capture_running else '',
        'capture_count' : inner_status.capture_count,
        'capture_motion_score': inner_status.capture_motion_score})

@app.route("/video_feed")
def video_feed():
    return Response(gen_frame(camera.Camera()),
            mimetype="multipart/x-mixed-replace; boundary=frame")
def gen_frame(camera):
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b"--frame\r\n" + b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        else:
            print("frame is none")

@app.route('/capture/trigger', methods=['POST'])
def capture_trigger():
    trigger = request.form.get('trigger','')
    capture_running = (trigger == 'start')
    capture_interval_sec = request.form.get("capture_interval_sec", "60", type=int)
    autostop_timer_hour = request.form.get("autostop_timer_hour", "0", type=int)
    autostop_timer_minute = request.form.get("autostop_timer_minute", "0", type=int)
    autostop_no_motion_enable = request.form.get("autostop_no_motion_enable", "off")
    if capture_running:
        dt_now = datetime.now()
        job_name = dt_now.strftime('%Y%m%d_%H%M%S')
        if param['capture_dir']=='{DEFAULT}':
            jobname_basedir=web_ui_path + '/../captured/frames'
        else:
            jobname_basedir = param['capture_dir']
        job_dir = jobname_basedir + '/' + job_name
        os.makedirs(job_dir, exist_ok=True)
        inner_status.capture_job_name = job_name
        inner_status.capture_job_dir = job_dir
        inner_status.capture_started_datetime = dt_now
        inner_status.capture_next_datetime = dt_now
        inner_status.capture_interval_sec = capture_interval_sec
        inner_status.capture_autostop_timer_sec = int(autostop_timer_hour)*3600 + int(autostop_timer_minute)*60
        inner_status.capture_autostop_no_motion = (autostop_no_motion_enable=='on')
        inner_status.capture_motion_score = 0.0
        inner_status.captuure_first_motion_waiting = (autostop_no_motion_enable=='on')
    else:
        inner_status.capture_running = False
        inner_status.capture_job_name = ''
        inner_status.capture_job_dir = ''
        inner_status.capture_interval_sec = 0
        inner_status.capture_autostop_timer_sec = 0
        inner_status.capture_autostop_no_motion = False
        inner_status.capture_started_datetime = None
        inner_status.capture_next_datetime = None
        inner_status.capture_count = 0
        inner_status.capture_motion_score = 0.0
        inner_status.captuure_first_motion_waiting = False

    inner_status.capture_running = capture_running
    return redirect(url_for('capture'))


class CaptureThread(threading.Thread):
    def __init__(self):
        super(CaptureThread, self).__init__()
        self.stop_event = threading.Event()
        self.curr_img = None
        self.prev_img = None
        self.autostop_no_motion_count = 0
        self.motion_capture_count = 0

    def stop(self):
        self.stop_event.set()

    def run(self):
        while True:
            if inner_status.capture_running:
                dt_now = datetime.now()

                # capture interval
                if inner_status.capture_next_datetime < dt_now:
                    frame = camera.Camera().get_frame()
                    if inner_status.captuure_first_motion_waiting:
                        # waiting with auto stop no motion
                        inner_status.capture_next_datetime = dt_now + timedelta(seconds=1)
                    else:
                        inner_status.capture_next_datetime = dt_now + timedelta(seconds=inner_status.capture_interval_sec)
                        with open('{}/{}.{}'.format(
                            inner_status.capture_job_dir, str(inner_status.capture_count).zfill(8), 'jpg'), "wb") as f:
                            f.write(frame)
                        inner_status.capture_count += 1

                    # auto stop no motion
                    if inner_status.capture_autostop_no_motion:
                        # cache prev frame
                        if self.motion_capture_count > 0:
                            self.prev_img = self.curr_img.copy()
                        # current frame decode jpg->cvmat
                        img_buf = np.frombuffer(frame, dtype=np.uint8)
                        self.curr_img = cv2.imdecode(img_buf, cv2.IMREAD_GRAYSCALE)
                        self.motion_capture_count += 1
                        #compare prev-curr frames
                        if self.motion_capture_count > 1:
                            score = self.compare_prev_frame(self.curr_img, self.prev_img)
                            inner_status.capture_motion_score = score
                            if param['capture_autostop_first_motion_threshold'] < score:
                                inner_status.captuure_first_motion_waiting = False
                            print("compare score", score)
                            if (score < param['capture_autostop_no_motion_threshold_score'] and
                                inner_status.captuure_first_motion_waiting == False):
                                print("no-motion detected.")
                                self.autostop_no_motion_count += 1
                                # consecutively exceed the threshold
                                if param['capture_autostop_no_motion_threshold_count'] <= self.autostop_no_motion_count:
                                    # auto stop
                                    print("no-motion auto stopped.")
                                    inner_status.capture_running = False
                            else:
                                print("motion detected.")
                                self.autostop_no_motion_count = 0

                # auto stop timer
                if inner_status.capture_autostop_timer_sec > 0:
                    if (inner_status.capture_started_datetime + 
                        timedelta(seconds=inner_status.capture_autostop_timer_sec)) < dt_now:
                        # auto stop
                        print("timer auto stopped.")
                        inner_status.capture_running = False

            else:
                self.autostop_no_motion_count = 0
                if self.stop_event.is_set():
                    break

            time.sleep(0.5)

    def compare_prev_frame(self, img0, img1):
        img_diff = img0.astype(int) - img1.astype(int)
        img_diff_abs = np.abs(img_diff)
        img_diff_bin = (img_diff_abs > 32) * 255
        pixel_number = np.size(img_diff_bin)
        pixel_sum = np.sum(img_diff_bin) / 255
        return float(pixel_sum) / float(pixel_number)

capture_thread = CaptureThread()
capture_thread.setDaemon(True)
capture_thread.start()
