ifname = 'eth1'


def get_local_ip(ifname):
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    ret = socket.inet_ntoa(inet[20:24])
    return socket.gethostname(), ret 

hostname, ip = get_local_ip(ifname)
TOKEN_APP = 'ccs'
TOKEN_KEY = 'fang.com'
API_SERVER = 'http://ccs.light.fang.com/api/v1/'
JENKINS_URL = 'http://%s/download/' % ip
CMDB = 'http://ops.light.fang.com/api/check/ip/?ip='
USER_NAME= 'jenkins'
USER_ID = 29
IDC_TAG = hostname.split('-')[0]
