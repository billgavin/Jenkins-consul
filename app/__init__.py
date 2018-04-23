from flask import Flask

app = Flask(__name__)
app.jinja_env.variable_start_string = '%%'
app.jinja_env.variable_end_string = '&&'

from app import views
