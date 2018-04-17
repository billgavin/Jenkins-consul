#!/usr/local/bin/python
# encoding; utf-8

from settings import CMDB
from settings import IDC_TAG
from consul import consul
from getinfo import upstreams

import sys
import requests
import re
import fire
import simplejson

scmd = {'sh': '/bin/sh', 'py': '/usr/local/bin/python'}


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

def getHostname(ip):
    res = requests.get(CMDB+ip)
    hosts = res.json()
    hostnames = []
    for h in hosts:
        hname = h.get('hostname')
        hostnames.append(hname)
    return hostnames

def consulPublish(src, desc, con_key):
    cl = consul()
    cluster = upstreams.get(con_key)
    hosts = {}
    for bk in cluster:
        idc = bk.get('idc')
        ip = bk.get('ip')
        for h in getHostname(ip):
            if idc not in h:
                continue
            hosts[h] = ip
    print('#' * 50)
    res = simplejson.loads(cl.upload(hosts.keys(), src, desc))
    if res.get('code') == 0:
        msg = res.get('msg')
        for k,v in msg.items():
            print('HOST: {} upload SUCCESS ! - {}'.format(hosts.get(k),v))
        print('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(hosts)) * 100.0))
    else:
        print('FAILD!!! - {} {}'.format(res.get('code'), res.get('msg')))
        sys.exit(res.get('code'))
    print('#' * 50)

def gethosts(con_key, flag):
    cluster = upstreams.get(con_key)
    hosts = []
    for bk in cluster:
        idc = bk.get('idc')
        ip = bk.get('ip')
        port = bk.get('port')
        lock = bk.get('lock')
        down = bk.get('down')
        bid = bk.get('backend_id')
        for case in switch(flag):
            if case(r'(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):\d{2,5}'):
                if flag == '{}:{}'.format(ip, port):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):\*'):
                if flag == '{}:{}'.format(ip, '*'):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):!\d{2,5}'):
                iflag, pflag = flag.split(':')
                if iflag == ip and pflag != '!{}'.format(port):
                    hosts.append((idc,ip,port, lock, down, bid))
                else:
                    continue
                break
            if case(r'!(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):\d{2,5}'):
                iflag, pflag = flag.split(':')
                if iflag != '!{}'.format(ip) and pflag == str(port):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'!(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):\*'):
                iflag, pflag = flag.split(':')
                if iflag != '!{}':
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'!(((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9]))\.){3}((1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])|([1-9][0-9])|([0-9])):!\d{2,5}'):
                if flag != '!{}:!{}'.format(ip, port):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'\*:\d{2,5}'):
                if flag == '*:{}'.format(port):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
                break
            if case(r'\*:!\d{2,5}'):
                if flag != '*:{}'.format(port):
                    hosts.append((idc, ip, port, lock, down, bid))
                else:
                    continue
            if case(r'\*|\*:\*'):
                hosts.append((idc, ip, port, lock, down, bid))
    return hosts

def consulCommand(script, con_key, flag='*'):
    cl = consul()
    s_t = script[-2:]
    for host in gethosts(con_key, flag):         
        idc, ip, port, lock, down, bid = host
        hostname = []
        for h in getHostname(ip):
            if idc not in h:
                continue
            hostname.append(h)
        if down == 0:
            print('#' * 50)
            res = simplejson.loads(cl.onoff('off', bid))
            if res.get('code') != 0:
                #print(unicode(res.get('msg'), 'utf-8'))
                sys.exit(res.get('code'))
            else:
                print('{}:{} is down.'.format(ip,port))
                down = 1
        else:
            print('{}:{} is already down yet.'.format(ip,port))
            print('#' * 50)
        res = simplejson.loads(cl.remoteCommand(hostname, '{} {}'.format(scmd.get(s_t), script)))
        if res.get('code', 0) != 0:
	    print('Error: {} -- {}'.format(res.get('code'),res.get('msg')))
        else:
	    for k, v in res.items():
                print('Host {}:'.format(ip))
                if v.get('retcode') != 0 :
		    print('Error: {} -- {}'.format(v.get('retcode'),v.get('ret')))
                else:
                    print('Success: {}'.format(v.get('ret')))

        if down == 1:
            res = simplejson.loads(cl.onoff('on', bid))
            if res.get('code') != 0:
                #print(unicode(res.get('msg'), 'utf-8'))
                sys.exit(res.get('code'))
            else:
                print('{}:{} is online.'.format(ip,port))
                down = 0
        else:
            print('{}:{} is already online.'.format(ip,port))
                
    
#################################################################

def publish(src, desc, *ips):
    hosts = {}
    cl = consul()
    for ip in ips:
        hnames = getHostname(ip)
        for h in hnames:
            if IDC_TAG not in h:
                continue
            hosts[h] = ip
    res = simplejson.loads(cl.upload(hosts.keys(), src, desc))
    if res.get('code') == 0:
        msg = res.get('msg')
        print('#' * 50)
        for k,v in msg.items():
            print('HOST: {} upload SUCCESS! - {}'.format(hosts.get(k),v))
        print('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(ips)) * 100.0))
    else:
        print('FAILD!!! - {} {}'.format(res.get('code'), res.get('msg')))
        sys.exit(res.get('code'))

def command(script, *ips):
    s_t = script[-2:]
    hosts = {}
    cl = consul()
    for ip in ips:
        hnames = getHostname(ip)
        for h in hnames:
            if IDC_TAG not in h:
                continue
            hosts[h] = ip
    res = simplejson.loads(cl.remoteCommand(hosts.keys(), '{} {}'.format(scmd.get(s_t),script)))
    if res.get('code', 0) != 0:
	print('Error: {} -- {}'.format(res.get('code'),res.get('msg')))
    else:
	for k, v in res.items():
            print('Host {}:'.format(hosts.get(k)))
            if v.get('retcode') != 0 :
		print('Error: {} -- {}'.format(v.get('retcode'),v.get('ret')))
            else:
                print('Success: {}'.format(v.get('ret')))

if __name__ == '__main__':
    fire.Fire()

