import os
import threading
import time
import queue
import cv2
import subprocess
import shutil
from flask import request, redirect, url_for, render_template, flash, make_response, jsonify
from web_ui import app
from web_ui import inner_status
from web_ui import param
from web_ui import web_ui_path

@app.route('/video')
def video():
    if param['capture_dir']=='{DEFAULT}':
        frames_basedir=web_ui_path + '/../captured/frames'
    else:
        frames_basedir = param['capture_dir']
    file_and_dirs = os.listdir(frames_basedir)
    frames_dirs = [f for f in file_and_dirs if os.path.isdir(os.path.join(frames_basedir, f))]
    frames_dirs.sort()
    selected_dir=''
    if len(frames_dirs)>0:
        #add frame count
        for i in range(len(frames_dirs)):
            frames_dir = frames_dirs[i]
            frames_path = frames_basedir + '/' + frames_dir
            file_count = len(os.listdir(frames_path))
            if file_count > 0:
                frames_dirs[i] = '{} (count: {})'.format(frames_dir, file_count)
            else:
                frames_dirs[i] = ''
        selected_dir = frames_dirs[-1]

    if param['video_dir']=='{DEFAULT}':
        video_basedir=web_ui_path + '/../captured/videos'
    else:
        video_basedir = param['video_dir']
    file_and_dirs = os.listdir(video_basedir)
    videos_files = [f for f in file_and_dirs if os.path.isfile(os.path.join(video_basedir, f)) and f!='.git_keep']
    videos_files.sort()
    selected_file = ''
    if len(videos_files)>0:
        selected_file = videos_files[-1]
    
    if not inner_status.encode_running:
        inner_status.encode_frame_rate = param['video_default_frame_rate']
    return render_template(
        'video.html', navi_title="video",
        frames_dirs = frames_dirs,
        selected_dir = selected_dir,
        videos_files = videos_files,
        selected_file = selected_file,
        encode_frame_rate = inner_status.encode_frame_rate)

@app.route('/encode/trigger', methods=['POST'])
def encode_trigger():
    frames_dir = request.form.get('frames_dir','')
    frame_rate = request.form.get('frame_rate', 10, type=int)
    if frames_dir=='':
        return redirect(url_for('video'))
    else:
        # remove frame count
        frames_dir = frames_dir.split(' ')[0]
    trigger = request.form.get('trigger', '')
    if trigger == 'encode':
        encode_thread.queue.put({'frames_dir':frames_dir, 'frame_rate':frame_rate})
    elif trigger == 'remove':
        print('remove', frames_dir)
        if param['capture_dir']=='{DEFAULT}':
            frames_basedir=web_ui_path + '/../captured/frames'
        else:
            frames_basedir = param['capture_dir']
        shutil.rmtree(frames_basedir+'/'+frames_dir)
    return redirect(url_for('video'))

@app.route('/encode/status')
def encode_status():
    return jsonify({
        'encode_running' : inner_status.encode_running,
        'encode_job_name' : inner_status.encode_job_name,
        'encode_job_framerate' : inner_status.encode_job_framerate})


@app.route('/video/trigger', methods=['POST'])
def video_trigger():
    videos_file = request.form.get('videos_file','')
    trigger = request.form.get('trigger', '')
    if videos_file=='':
        return redirect(url_for('video'))
    if trigger == 'remove':
        print('remove', videos_file)
        if param['video_dir']=='{DEFAULT}':
            video_basedir=web_ui_path + '/../captured/videos'
        else:
            video_basedir = param['video_dir']
        os.remove(video_basedir+'/'+videos_file)
    return redirect(url_for('video'))


@app.route('/video/download', methods=['GET'])
def video_download():
    filename = request.args.get('filename','')
    if filename=='':
        return redirect(url_for('video'))
    if param['video_dir']=='{DEFAULT}':
        video_basedir=web_ui_path + '/../captured/videos'
    else:
        video_basedir = param['video_dir']
    response = make_response()
    response.data = open(video_basedir+'/'+filename, "rb").read()
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    response.mimetype = 'video/mp4'
    return response

class EncodeThread(threading.Thread):
    def __init__(self):
        super(EncodeThread, self).__init__()
        self.stop_event = threading.Event()
        self.queue = queue.Queue()

    def stop(self):
        self.stop_event.set()

    def run(self):
        while True:
            if not self.queue.empty():
                job = self.queue.get()
                frames_dir = job['frames_dir']
                frame_rate = job['frame_rate']
                inner_status.encode_running = True
                inner_status.encode_job_name = frames_dir
                inner_status.encode_job_framerate = frame_rate
                if param['capture_dir']=='{DEFAULT}':
                    frames_basedir=web_ui_path + '/../captured/frames'
                else:
                    frames_basedir = param['capture_dir']
                if param['video_dir']=='{DEFAULT}':
                    video_basedir=web_ui_path + '/../captured/videos'
                else:
                    video_basedir = param['video_dir']
                frames_full_dir = frames_basedir + '/' + frames_dir
                file_and_dirs = os.listdir(frames_full_dir)
                frame_files = [f for f in file_and_dirs if os.path.isfile(os.path.join(frames_full_dir, f)) and f!='.git_keep']

                frame = cv2.imread(frames_full_dir+'/'+frame_files[0])
                height, width, channels = frame.shape[:3]
                subprocess.run(('ffmpeg' ,
                    '-loglevel', 'warning',
                    '-y',
                    '-framerate', str(frame_rate),
                    '-i', frames_full_dir+'/%8d.jpg',
                    '-vframes', str(len(frame_files)),
                    '-vf', 'scale={0}:{1},format=yuv420p'.format(width, height),
                    '-vcodec', 'libx264',
                    '-r', str(frame_rate),
                    '{}/{}_{}fps.mp4'.format(video_basedir, frames_dir, frame_rate)))
            else:
                inner_status.encode_running = False
            if self.stop_event.is_set():
                break
            time.sleep(0.5)

encode_thread = EncodeThread()
encode_thread.setDaemon(True)
encode_thread.start()
