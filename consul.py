#!/usr/local/bin/python
# coding: utf-8

import requests
import fire
import simplejson as json
import auth
from settings import *

class consul():
    

    def __init__(self):
        self.token = auth.gettoken()
        self.upload_file = API_SERVER + 'uploadfile/'
        self.consul_url = API_SERVER + 'nginx/'

    def getInfo(self, *args):
        url = self.consul_url + '/'.join(args) + '/'
        resp = requests.get(url, params={'auth_token': self.token})
        if resp.status_code == requests.codes.ok:
            return resp.content
        else:
            resp.raise_for_status()

    def onoff(self, opt, ids):
        resp = requests.get('{}onoff/{}/{}/'.format(self.consul_url, opt, ids),\
                 params={'auth_token': self.token})
        if resp.status_code == requests.codes.ok:
            return resp.content
        else:
            resp.raise_for_status()


    def upload(self, hosts, src, desc):
        data = {
            'host': hosts,
            'url': JENKINS_URL + src,
            'dest': desc
        }
        res = requests.post(API_SERVER + 'uploadfile/', data=json.dumps(data), \
                params={'auth_token': self.token})
        #print(res.url)
        if res.status_code == requests.codes.ok:
            return res.content
        else:
            res.raise_for_status()
    
    def remoteCommand(self, hosts, command, mode='sync'):

        data = {
            'action': mode,
            'hosts': hosts,
            'args': command
        }
        res = requests.post(API_SERVER + 'salt/execcmd/', data=json.dumps(data), \
                params={'auth_token': self.token})
        #print(res.url)
        #print(data)
        if res.status_code == requests.codes.ok:
            return res.content
        else:
            res.raise_for_status()
    

if __name__ == '__main__':
	fire.Fire()
