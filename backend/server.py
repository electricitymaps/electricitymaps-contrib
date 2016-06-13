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


@app.route('/realtime', methods=['GET', 'OPTIONS'])
def realtime_GET():
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

@app.route('/data/<path:path>')
def data_GET(path, methods=['GET', 'OPTIONS']):
    return flask.send_from_directory('data', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
