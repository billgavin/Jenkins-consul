#!/bin/python
# encoding; utf-8

from settings import CMDB
from settings import IDC_TAG
from settings import SALT_CHECK
from consul import consul
#from getinfo import upstreams
from tools import get_logger, switch

import sys
import os
import requests
import re
import fire
import simplejson
import time

scmd = {'sh': '/bin/sh', 'py': '/usr/local/bin/python'}


logger = get_logger('Jenkins publish', '/www/logs/', True)


def getHostname(ip):
    res = requests.get(CMDB+ip)
    hosts = res.json()
    if not hosts:
        logger.error('%s: cant find the host.' % ip)
        sys.exit(4)
    hostnames = []
    for h in hosts:
        hname = h.get('hostname')
        email = h.get('email')
        if IDC_TAG not in hname:
            continue
        res = requests.get(SALT_CHECK, params={'key': hname})
        flag = eval(res.content)
        if flag:   
            hostnames.append(hname)
        else:
            logger.error('{} salt agnet connection error, send the message to {}'.format(ip, email))
            sys.exit(3)
    print(hostnames)
    return hostnames

def consulPublish(src, desc, con_key):
    #filepath = '/opt/local/jenkins/workspace' + src
    #assert os.path.exists(filepath), 'File: "%s" is not exists!' % filepath
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
    print(res)
    if res.get('code') == 0:
        msg = res.get('msg')
        for k,v in msg.items():
            logger.info('HOST: {} upload SUCCESS ! - {}'.format(hosts.get(k),v))
        logger.info('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(hosts)) * 100.0))
    else:
        logger.error('FAILED!!! - {} {}'.format(res.get('code'), res.get('msg')))
        print('FAILED!!! - {} {}'.format(res.get('code'), res.get('msg')))
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
            print(res)
            if res.get('code') != 0:
                sys.exit(res.get('code'))
            else:
                logger.info('{}:{} is down.'.format(ip,port))
                down = 1
        else:
            logger.info('{}:{} is already down yet.'.format(ip,port))
            print('#' * 50)
        res = simplejson.loads(cl.remoteCommand(hostname, '{} {}'.format(scmd.get(s_t), script)))
        print(res)
        res_msg = res.get(hostname[0])
        retcode = res_msg.get('retcode')
        msg = res_msg.get('ret')
        if retcode != 0:
            logger.error('{}:{} Failed!!! \n{}'.format(ip, port, msg))
            print('{}:{} Failed!!! \n{}'.format(ip, port, msg))
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
    #filepath = '/opt/local/jenkins/workspace' + src
    #assert os.path.exists(filepath), 'File: "%s" is not exists!' % filepath
    hosts = {}
    cl = consul()
    for ip in ips:
        hnames = getHostname(ip)
        for h in hnames:
            hosts[h] = ip
    res = simplejson.loads(cl.upload(hosts.keys(), src, desc))
    print(res)
    if res.get('code') == 0:
        msg = res.get('msg')
        print('#' * 50)
        for k,v in msg.items():
            logger.info('HOST: {} upload SUCCESS! - {}'.format(hosts.get(k),v))
        logger.info('{:.2f}% upload SUCCESS!'.format(float(len(msg)) / float(len(ips)) * 100.0))
    else:
        logger.error('FAILED!!! - {} {}'.format(res.get('code'), res.get('msg')))
        print('FAILED!!! - {} {}'.format(res.get('code'), res.get('msg')))
        sys.exit(res.get('code'))

def command(script, *ips):
    s_t = script[-2:]
    hosts = {}
    cl = consul()
    for ip in ips:
        hnames = getHostname(ip)
        for h in hnames:
            hosts[h] = ip
    res = simplejson.loads(cl.remoteCommand(hosts.keys(), '{} {}'.format(scmd.get(s_t),script)))
    print(res)
    if not res:
        logger.error(res)
        sys.exit(5)
    for h, msg in res.items():
        ip = hosts.get(h)
        retcode = msg.get('retcode')
        ret = msg.get('ret')
        if retcode != 0:
            logger.error('{}:{} Failed!!! \n{}'.format(ip, h, ret))
            print('{}:{} Failed!!! \n{}'.format(ip, h, ret))
            sys.exit(retcode)
        else:
            logger.info('{}:{} Success.\n{}'.format(ip, h, ret))


def k8s_deploy(deployment, image, env):
    '''
        kubectl set image  deployments/{ebcenter-test} {ebcenter-test}={dockerhub.3g.fang.com/ebcenter/ebcenter_app_v321:v321}  -n {test-env}
        salt  xg-o-k8sm1v  cmd.run
    '''
    cl = consul()
    command = 'kubectl set image deployments/{a} {a}={b} -n {c}'.format(a=deployment, b=image, c=env)
    print(command)
    sh_file = '/k8s_deploy/{}-{}.sh'.format(deployment, time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))
    with open('/opt/local/jenkins/workspace' + sh_file, 'w') as f:
        f.write(command)
    res = simplejson.loads(cl.upload(['xg-o-k8sm1v'], sh_file, '/tmp' + sh_file))
    print('upload')
    print(res)
    if res.get('code') == 0:
        msg = res.get('msg')
        cmd_res = simplejson.loads(cl.remoteCommand(['xg-o-k8sm1v'], '/tmp' + sh_file))
        print('command')
        print(cmd_res)
        if not cmd_res:
            logger.error(res)
            sys.exit(5)
        for h, msg in cmd_res.items():
            retcode = msg.get('retcode')
            ret = msg.get('ret')
            if retcode != 0:
                logger.error('{} Failed!!! \n{}'.format('xg-o-k8sm1v', ret))
                print('{} Failed!!! \n{}'.format('xg-o-k8sm1v', ret))
                sys.exit(retcode)
            else:
                logger.info('{} Success.\n{}'.format('xg-o-k8sm1v', ret))
    else:
        logger.error('FAILED!!! - {} {}'.format(res.get('code'), res.get('msg')))
        sys.exit(res.get('code'))
    

if __name__ == '__main__':
    fire.Fire()

