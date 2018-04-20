from logbook import Logger, StreamHandler, TimedRotatingFileHandler
from logbook.more import ColorizedStderrHandler
import logbook
import sys
import fire
import os


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

if __name__ == '__main__':
	fire.Fire()
