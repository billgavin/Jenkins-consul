#!/usr/local/bin/python
# encoding; utf-8

from settings import CMDB
from settings import IDC_TAG
from consul import consul
from getinfo import upstreams
from tools import get_logger, switch

import sys
import requests
import re
import fire
import simplejson

scmd = {'sh': '/bin/sh', 'py': '/usr/local/bin/python'}


logger = get_logger('Jenkins publish', '/www/logs/', True)


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
            logger.info('HOST: {} upload SUCCESS ! - {}'.format(hosts.get(k),v))
        logger.info('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(hosts)) * 100.0))
    else:
        logger.error('FAILD!!! - {} {}'.format(res.get('code'), res.get('msg')))
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
                sys.exit(res.get('code'))
            else:
                logger.info('{}:{} is down.'.format(ip,port))
                down = 1
        else:
            logger.info('{}:{} is already down yet.'.format(ip,port))
            print('#' * 50)
        res = simplejson.loads(cl.remoteCommand(hostname, '{} {}'.format(scmd.get(s_t), script)))
        res_msg = res.get(hostname[0])
        retcode = res_msg.get('retcode')
        msg = res_msg.get('ret')
        if retcode != 0:
            logger.error('{}:{} Filed!!! \n{}'.format(ip, port, msg))
            sys.exit(retcode)
        else:
            logger.info('{}:{} Success.\n{}'.format(ip, port, msg))
        if down == 1:
            res = simplejson.loads(cl.onoff('on', bid))
            if res.get('code') != 0:
                sys.exit(res.get('code'))
            else:
                logger.info('{}:{} is online.'.format(ip,port))
                down = 0
        else:
            logger.info('{}:{} is already online.'.format(ip,port))
                
    
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
            logger.info('HOST: {} upload SUCCESS! - {}'.format(hosts.get(k),v))
        logger.info('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(ips)) * 100.0))
    else:
        logger.error('FAILD!!! - {} {}'.format(res.get('code'), res.get('msg')))
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
    for hostname, msg in res.items():
        ip = hosts.get(hostname)
        retcode = msg.get('retcode')
        ret = msg.get('ret')
        if retcode != 0:
            logger.error('{}:{} Filed!!! \n{}'.format(ip, hostname, ret))
            sys.exit(retcode)
        else:
            logger.info('{}:{} Success.\n{}'.format(ip, hostname, ret))
if __name__ == '__main__':
    fire.Fire()

