"""
Flask API for the service.
"""

from flask import Flask, jsonify, redirect, url_for, request

from .version import __version__
from .proxy import Proxy, SessionThreadPool
from .log import init_logging
from .geoip import GeoipDB


init_logging()
session_pool = SessionThreadPool()
app = Flask(__name__)


@app.route('/')
def index():
    """
    Redirect / to /list.
    """
    return redirect('/api/v1' + url_for('list_'))


@app.route('/list')
def list_():
    """
    Returns list of active proxies.
    """
    count = int(request.args.get('count', '0'))
    country = request.args.get('country', '').upper()
    region = request.args.get('region', '')
    city = request.args.get('city', '')
    score = float(request.args.get('score', '0.0'))
    ordered = bool(request.args.get('ordered', ''))
    format_ = request.args.get('format', 'json')

    session = session_pool.get()
    result = Proxy.list_active(session)

    if country:
        result = filter(lambda e: e.country == country, result)
    if region:
        result = filter(lambda e: e.region == region, result)
    if city:
        result = filter(lambda e: e.city == city, result)
    if score:
        result = filter(lambda e: e.score >= score, result)
    if ordered:
        result = sorted(result, key=lambda e: e.score, reverse=True)
    if count:
        result = list(result)[:count]

    if format_ == 'plain':
        result = map(Proxy.__repr__, result)
        return '\n'.join(result), 200, {'Content-Type': 'text/plain'}
    else:
        result = map(Proxy.as_dict, result)
        return jsonify(result=list(result))


@app.route('/check/<proxy>')
def check(proxy):
    """
    Checks passed proxy.
    """
    host, port = proxy.split(':', 1)
    proxy_obj = Proxy(host=host, port=int(port))
    result = proxy_obj.check()
    return jsonify(host=host, port=port, result=result)


@app.route('/geo/<host>')
def geo(host):
    """
    Returns geo information about the host.
    """
    geo_info = GeoipDB.get_instance().get_info(host)
    return jsonify(host=host, geo=geo_info)


@app.route('/version')
def version():
    """
    Returns version of the project.
    """
    return jsonify(version=__version__)


@app.route('/licenses')
def licenses():
    """
    Returns licenses used in the project.
    """
    return jsonify(
        geo="Geo data is taken from https://db-ip.com/ under " \
            "Creative Commons Attribution 4.0 International License",
    )
