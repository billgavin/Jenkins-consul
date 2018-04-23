import sys
from app import app
from flask import request, render_template, redirect, url_for
sys.path.append('..')
from getinfo import upstreams
import simplejson

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Upstreams', records=simplejson.dumps(upstreams))
