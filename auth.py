#!/usr/loca/bin/python
''' create an auth_key'''
import time
import base64
import pyDes
from settings import USER_NAME, USER_ID, TOKEN_APP, TOKEN_KEY


def gettoken():
    ''' create an auth_key'''
    sign = '{}|{}|{}|{}'.format(USER_NAME, USER_ID, TOKEN_APP, int(time.time()))
    k = pyDes.des(TOKEN_KEY, pyDes.CBC, TOKEN_KEY, pad=None, padmode=pyDes.PAD_PKCS5)
    return base64.urlsafe_b64encode(k.encrypt(sign))
