#!/usr/local/bin/python

from settings import CMDB
from consul import consul
from tools import dump_disk

import simplejson
import sys


def get_idcs():
    cl = consul()
    idcnames = {}
    idcs = simplejson.loads(cl.getInfo('idc')).get('msg')
    for idc in idcs:
        idc_tag = idc.get('tag')
        idc_id = idc.get('id')
        idcnames[idc_id] = idc_tag

    business = simplejson.loads(cl.getInfo('business')).get('msg')
    idcs = {}
    for bs in business:
        tag = bs.get('tag')
        idc = bs.get('idc')
        idc_tag = idcnames.get(idc)
        idcs[tag] = idc_tag
    return idcs

def get_upstreams():
    cl = consul()
    clusters = {}
    idcs = get_idcs()
    res = simplejson.loads(cl.getInfo('upstream')).get('msg')
    for upstream in res:
        stat = upstream.get('stat')
        if not stat:
            continue
        cluster = upstream.get('cluster')
        parent = upstream.get('parent')
        cid = upstream.get('id')
        con_key = '{}/{}'.format(parent, cluster)
        info = clusters.get(cid, {})
        info = {
            'consul': con_key,
            'idc': idcs.get(parent)
        }
        clusters[cid] = info

    upstreams = {}
    backends = simplejson.loads(cl.getInfo('backend')).get('msg')
    for bs in backends:
        uid = bs.get('upstream')
        info = clusters.get(uid)
        conkey = info.get('consul')
        idc = info.get('idc')
        ip, port = bs.get('ip').split(':')
        bid = bs.get('id')
        down = bs.get('down')
        lock = bs.get('lock')
        us = upstreams.get(conkey, [])
        us.append({
            'backend_id': bid,
            'ip': ip,
            'port': port,
            'down': down,
            'lock': lock,
            'idc': idc
        })
        upstreams[conkey] = us
    return upstreams

def main():

    idcf = 'pickle/idcs.pkl'
    idcc = dump_disk(idcf)
    idcs = idcc.get()
    if not idcs:
        idcs = get_idcs()
        idcc.set(idcs)

    usf = 'pickle/upstreams.pkl'
    usc = dump_disk(usf)
    upstreams = usc.get()
    if not upstreams:
        upstreams = get_upstreams()
        usc.set(upstreams)

    return idcs, upstreams

if __name__ == '__main__':
    idcs, upstreams = main()
    print(simplejson.dumps(eval(sys.argv[1])))
