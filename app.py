#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import datetime
import json
from flask import Flask, session, redirect, url_for, render_template, request, flash

logging.basicConfig(level=logging.INFO)


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the 
    front-end server to add these headers, to let you quietly bind 
    this to a URL other than / and to an HTTP scheme that is 
    different than what is used locally.

    In NginX:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.config['SECRET_KEY'] = 'ToM0rroW3yXsg5sHH!jmN]LWZ/$?RT'

with open('config.json', 'rt') as config_file:
    config = json.loads(config_file.read())
logging.info('Load configuration: {}'.format(config))

app.config.update(config)

app.secret_key = app.config['SECRET_KEY']
epoch = datetime.datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0


def logged():
    success = False
    if 'username' in session:
        if 'datetime' in session:
            now = unix_time_millis(datetime.datetime.now())
            if (now - session['datetime']) < app.config['SESSION_IDLE_SECONDS'] * 1000:
                session['datetime'] = now
                success = True
            else:
                flash('Expiration de la connexion')
    return success


@app.route("/")
def index():
    if not logged():
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == app.config['USERNAME'] and request.form['password'] == app.config['PASSWORD']:
            session['username'] = request.form['username']
            session['datetime'] = unix_time_millis(datetime.datetime.now())
            return redirect(url_for('index'))
        else:
            flash('Utilisateur ou mot de passe incorrect')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('datetime', 0)
    return redirect(url_for('index'))


@app.route("/delete")
def delete():
    flash("Effacement des données en cours...")
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
