import json
import logging
import logging.handlers as handlers
import sys
import time

from flask import Flask, request
from werkzeug.utils import secure_filename

import compare_image
import detect_face

with open("config.json") as extConfigFile:
    extConfig = json.load(extConfigFile)

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# Here we define our formatter
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s [%(processName)s] [%(threadName)s] %(name)s:%(filename)s %(lineno)s : %(message)s')

logHandler = handlers.TimedRotatingFileHandler(extConfig['logger']['file'], when=extConfig['logger']['rollWhen'],
                                               interval=extConfig['logger']['interval'],
                                               backupCount=extConfig['logger']['backupCount'])
logHandler.setLevel(logging.DEBUG)
logHandler.setFormatter(formatter)

logger.addHandler(logHandler)

app = Flask(__name__)
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None


@app.route('/api/v1/compare_faces', methods=['POST'])
def compare_faces():
    logger.info('------------------------------')
    logger.info('incoming compare_faces request')
    target = request.files['target']
    user_id = request.headers.get('user_id')
    logger.info("request user id: %s", user_id)
    tolerance = request.form['tolerance']
    faces = request.files.getlist("faces")
    target_filename = secure_filename(target.filename)
    response = []
    for face in faces:
        start = time.time()
        distance, result = compare_image.main(target, face, tolerance)
        end = time.time()
        time_taken = round(end - start, 3)
        logger.info("time taken to compare %s with %s : %s", face.filename, target_filename, time_taken)
        json_content = {
            'result': str(result),
            'distance': round(distance, 2),
            'time_taken': time_taken,
            'target': target_filename,
            'face': secure_filename(face.filename)
        }
        response.append(json_content)
    python2json = json.dumps(response)
    logger.info('finished processing compare_faces request')
    logger.info(python2json)
    return app.response_class(python2json, content_type='application/json')


@app.route('/api/v1/detect_faces', methods=['POST'])
def detect_faces():
    logger.info('------------------------------')
    logger.info('incoming detect_faces request ')
    faces = request.files.getlist("faces")
    user_id = request.headers.get('user_id')
    logger.info("request user id: %s", user_id)
    # target_filename=secure_filename(target.filename)
    response = []
    for face in faces:
        start = time.time()
        _, result = detect_face.get_coordinates(face)
        end = time.time()
        time_taken = round(end - start, 3)
        logger.info("Time taken for %s : %s", face.filename, time_taken)
        json_contect = {
            'coordinates': result,
            'time_taken': time_taken,
            'image_name': secure_filename(face.filename)
        }
        response.append(json_contect)
    python2json = json.dumps(response)
    logger.info('finished processing detect_faces request')
    logger.info(python2json)
    return app.response_class(python2json, content_type='application/json')


if __name__ == "__main__":
    logger.info('Loaded Configurations from config.json')
    logger.info(extConfig)
    app.run(debug=extConfig['debug'], host=extConfig['hostname'], port=extConfig['port'])
