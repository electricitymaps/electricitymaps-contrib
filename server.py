import arrow, flask, json, os, pymongo

from flask_cors import CORS

ENV = os.environ.get('ENV', 'DEBUG')
PORT = 8000

app = flask.Flask(__name__, static_folder='data')
app.debug = (ENV == 'DEBUG')
CORS(app)

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['electricity']
col = db['realtime']

def bson_measurement_to_json(obj):
    obj['_id'] = str(obj['_id'])
    obj['datetime'] = arrow.get(obj['datetime']).isoformat()
    return obj


@app.route('/production', methods=['GET', 'OPTIONS'])
def production_GET():
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
def solar_GET():
    return flask.send_from_directory('data', 'solar.json')

@app.route('/wind', methods=['GET', 'OPTIONS'])
def wind_GET():
    return flask.send_from_directory('data', 'wind.json')

@app.route('/data/<path:path>', methods=['GET', 'OPTIONS'])
def data_GET(path):
    return flask.send_from_directory('data', path)

@app.route('/')
def index_GET():
    return flask.send_from_directory('', 'index.html')

@app.route('/vendor/<path:path>', methods=['GET', 'OPTIONS'])
def vendor_GET(path):
    return flask.send_from_directory('vendor', path)

@app.route('/app/<path:path>', methods=['GET', 'OPTIONS'])
def app_GET(path):
    return flask.send_from_directory('app', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
