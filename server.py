import arrow, flask, json, os, pymongo

from flask_cors import CORS

ENV = os.environ.get('ENV', 'development').lower()
PORT = 8000

app = flask.Flask(__name__, static_folder='data')
app.debug = (ENV == 'development')
CORS(app)

# Stats
import statsd
statsd.init_statsd({
    'STATSD_HOST': os.environ.get('STATSD_HOST', 'localhost'),
    'STATSD_BUCKET_PREFIX': 'electricymap_api'
})

# Loghandler in production mode
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        mailhost=('smtp.mailgun.org', 587),
        fromaddr='Application Bug Reporter <noreply@mailgun.com>',
        toaddrs=['olivier.corradi@gmail.com'],
        subject='Electricity Map Flask Error',
        credentials=(os.environ.get('MAILGUN_USER'), os.environ.get('MAILGUN_PASSWORD'))
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    logging.getLogger('statsd').addHandler(logging.StreamHandler())

client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client['electricity']
col = db['realtime']

def bson_measurement_to_json(obj):
    obj['_id'] = str(obj['_id'])
    obj['datetime'] = arrow.get(obj['datetime']).isoformat()
    return obj


@app.route('/production', methods=['GET', 'OPTIONS'])
@statsd.StatsdTimer.wrap('production_GET')
def production_GET():

    statsd.increment('production_GET')
    objs = col.aggregate([
        {'$group': {'_id': '$countryCode', 'lastDocument': {'$last': '$$CURRENT'}}}
    ])
    objs = map(bson_measurement_to_json,
        map(lambda o: o['lastDocument'], list(objs)))
    data = {obj['countryCode']: obj for obj in objs if 'countryCode' in obj}
    return flask.jsonify({
        'status': 'ok',
        'data': data
    })

@app.route('/solar', methods=['GET', 'OPTIONS'])
@statsd.StatsdTimer.wrap('solar_GET')
def solar_GET():
    statsd.increment('solar_GET')
    return flask.send_from_directory('data', 'solar.json')

@app.route('/wind', methods=['GET', 'OPTIONS'])
@statsd.StatsdTimer.wrap('wind_GET')
def wind_GET():
    statsd.increment('wind_GET')
    return flask.send_from_directory('data', 'wind.json')

@app.route('/data/<path:path>', methods=['GET', 'OPTIONS'])
@statsd.StatsdTimer.wrap('data_GET')
def data_GET(path):
    statsd.increment('data_GET')
    return flask.send_from_directory('data', path)

@app.route('/')
@statsd.StatsdTimer.wrap('index_GET')
def index_GET():
    statsd.increment('index_GET')
    return flask.send_from_directory('', 'index.html')

@app.route('/style.css')
def style_GET():
    return flask.send_from_directory('', 'style.css')

@app.route('/vendor/<path:path>', methods=['GET', 'OPTIONS'])
def vendor_GET(path):
    return flask.send_from_directory('vendor', path)

@app.route('/app/<path:path>', methods=['GET', 'OPTIONS'])
def app_GET(path):
    return flask.send_from_directory('app', path)

@app.route('/health', methods=['GET', 'OPTIONS'])
@statsd.StatsdTimer.wrap('health_GET')
def health_GET():
    statsd.increment('health_GET')
    return flask.jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
