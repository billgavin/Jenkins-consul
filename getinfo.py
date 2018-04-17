#!/usr/local/bin/python

from settings import CMDB
from consul import consul

import simplejson
import sys

cl = consul()

business = simplejson.loads(cl.getInfo('business')).get('msg')
idcs = {}
for bs in business:
    tag = bs.get('tag')
    bid = bs.get('id')
    idcid = bs.get('idc')
    res = simplejson.loads(cl.getInfo('idc', str(idcid))).get('msg')
    idc = res.get('tag')
    idcname = res.get('idc')
    idcs[tag] = idc

backends = simplejson.loads(cl.getInfo('backend')).get('msg')
upstreams = {}
for bs in backends:
    upstream_id = bs.get('upstream')
    upstream = simplejson.loads(cl.getInfo('upstream',str(upstream_id)))
    if upstream.get('code') != 0:
        continue
    upstream = upstream.get('msg')
    cluster = upstream.get('cluster')
    parent = upstream.get('parent')
    stat = upstream.get('stat')
    cid = upstream.get('id')
    con_key = '{}/{}'.format(parent, cluster)
    ipp = bs.get('ip').split(':')
    us = upstreams.get(con_key, [])
    info = {}
    info['backend_id'] = bs.get('id')
    info['ip'] = ipp[0]
    info['port'] = ipp[1]
    info['down'] = bs.get('down')
    info['lock'] = bs.get('lock')
    info['idc'] = idcs.get(parent)
    us.append(info)
    upstreams[con_key] = us

if __name__ == '__main__':
    print(simplejson.dumps(eval(sys.argv[1])))
