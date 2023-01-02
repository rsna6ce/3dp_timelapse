import pdb

class Status():
    def __init__(self):
        self.capture_running = False
        self.capture_job_name = ''
        self.capture_job_dir = ''
        self.capture_interval_sec = 0
        self.capture_autostop_timer_sec = 0
        self.capture_autostop_no_motion = True
        self.capture_started_datetime = None
        self.capture_next_datetime = None
        self.capture_count = 0
        self.encode_running = False
        self.encode_job_name = ''
        self.encode_job_framerate = 0
        self.encode_framerate = 10
