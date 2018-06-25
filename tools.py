from logbook import Logger, StreamHandler, TimedRotatingFileHandler
from logbook.more import ColorizedStderrHandler
import socket, fcntl, struct
import logbook
import sys
import fire
import os
import re
import time
import pickle


class switch(object):


    def __init__(self, value, flag=0):
        '''
        re.S DOTALL
        re.I IGNORECASE
        re.L LOCALE
        re.M MULTILINE
        re.X VERBOSE
        re.U
        '''
        self.value = value
        self.fall = False
        self.flag = flag

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, arg=''):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not arg:
            return True
        elif re.search(arg, self.value, self.flag) is not None:
            self.fall = True
            return True
        else:
            return False

class dump_disk:

    def __init__(self, dump_file, timeout=60*60*24):
        self.dump_file = os.path.join(os.path.dirname(__file__), dump_file)
        self.timeout = timeout

    def set(self,obj):
        with open(self.dump_file, 'wb') as f:
            pickle.dump(obj, f)

    def get(self):
        if not os.path.exists(self.dump_file):
            return None
        mtime = os.path.getmtime(self.dump_file)
        if (time.time() - mtime) >= self.timeout:
            return None
        with open(self.dump_file, 'rb') as f:
            return pickle.load(f)

def get_logger(name='LOGBOOK', log_path='', file_log=False):
	logbook.set_datetime_format('local')
	ColorizedStderrHandler(bubble=True).push_application()
	log_dir = os.path.join('log') if not log_path else log_path
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)
	if file_log:
		TimedRotatingFileHandler(os.path.join(log_dir, '%s.log' % name.lower()), date_format='%Y-%m-%d', bubble=True).push_application()
	return Logger(name)

def get_path(path):
	return os.path.join(os.path.dirname(__file__), path)

def get_local_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    ret = socket.inet_ntoa(inet[20:24])
    return socket.gethostname(), ret 

if __name__ == '__main__':
	fire.Fire()
