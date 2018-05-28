from tools import get_local_ip
ifname = 'eth1'
hostname, ip = get_local_ip(ifname)
TOKEN_APP = 'ccs'
TOKEN_KEY = 'fang.com'
API_SERVER = 'http://ccs.light.fang.com/api/v1/'
JENKINS_URL = 'http://%s/download' % ip
CMDB = 'http://ops.light.fang.com/api/check/ip/?ip='
SALT_CHECK = 'http://saltnew.light.soufun.com/ping/'
USER_NAME= 'jenkins'
USER_ID = 29
IDC_TAG = hostname.split('-')[0]
