from datetime import datetime
from flask import Flask, request, jsonify, make_response, abort, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
from http import HTTPStatus
import logging
from threading import Lock

import tohil
from . import message_handlers
from . import wifi_helpers

APP_NAME = 'piaware-configurator'

app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False

socketio = SocketIO(app, cors_allowed_origins="*")
log_thread=None
stop_thread = False
client_states = {}
state_lock = Lock()

@app.before_first_request
def before_first_request_func():
    """ Initialization of Tcl package dependencies and logger

    """
    tohil.eval('package require fa_piaware_config')
    tohil.eval('catch {package require fa_flightfeeder_config}')
    tohil.eval('package require fa_sudo')
    tohil.eval('package require fa_sysinfo')
    tohil.eval('::fa_piaware_config::new_combined_config piawareConfig')
    tohil.eval('catch {::fa_flightfeeder_config::flightfeeder_combined_config flightfeederConfig}')
    tohil.eval('catch {::fa_flightfeeder_config::flightfeeder_volatile_network_config flightfeederNetworkConfig}')

@app.errorhandler(404)
def not_found_error(error):
    response = {"error": "Resource not found"}
    return jsonify(response), 404

@app.route('/configurator/', methods=["POST"])
def configurator():
    """Endpoint to serve POST requests. Only accepts content-type application/json.

    Returns a Flask Response object
    """

    json_payload = validate_json(request)

    response = process_json(json_payload)

    return response

@app.route('/system/status', methods=["GET"])
def system_status():
    response = dict()

    try:
        utcnow = datetime.utcnow()
        system_time_utc_str = f"{utcnow.strftime('%H:%M')} UTC"
    except:
        app.logger.error('Error retrieving system time')
        system_time_utc_str = None

    try:
        total_tx_bytes, total_rx_bytes = wifi_helpers.get_transfer_rate_statistics()
    except:
        app.logger.error('Error retrieving networking transfer rate statistics')
        total_tx_bytes = total_rx_bytes = None

    response['system_time'] = system_time_utc_str
    response['total_tx_bytes'] = total_tx_bytes
    response['total_rx_bytes'] = total_rx_bytes

    return make_response(jsonify(response), 200)

@app.route('/piaware/status', methods=["GET"])
def piaware_status():
    """Endpoint to read piaware status.json if it exists

    """

    file_path = "/var/run/piaware/status.json"
    try:
        return send_file(file_path, mimetype='application/json')
    except FileNotFoundError:
        response = {'error': 'Could not read PiAware status.json'}
        return make_response(jsonify(response), 404)

@app.route('/flightfeeder/status', methods=["GET"])
def flightfeeder_status():
    """Endpoint to read flightfeeder status.json if it exists

    """

    file_path = "/var/run/flightfeeder/status.json"
    try:
        return send_file(file_path, mimetype='application/json')
    except FileNotFoundError:
        response = {'error': 'Could not read FlightFeeder status.json'}
        return make_response(jsonify(response), 404)

@socketio.on('connect')
def handle_connect():
    ''' Socketio connect event

    '''
    join_room(request.sid)

    with state_lock:
        if request.sid not in client_states:
            client_states[request.sid] = {'log_thread': None, 'stop_thread': False}

        if client_states[request.sid]['log_thread'] is None:
            # Create a thread for that client
            client_states[request.sid]['log_thread'] = socketio.start_background_task(stream_piaware_log_file, request.sid)
            app.logger.info(f'Accepted client connection')

@socketio.on('disconnect')
def handle_disconnect():
    ''' Socketio disconnect event

    '''
    with state_lock:
        if request.sid in client_states:
            client_states[request.sid]['log_thread'] = None
            client_states[request.sid]['stop_thread'] = True
            del client_states[request.sid]

    leave_room(request.sid)
    app.logger.info(f'Client disconnected')

def stream_piaware_log_file(client_sid):
    ''' Streams piaware.log by periodically reading the file and emitting the data via a web socket.
        This will periodically seek to EOF to determine if there are new lines to be read.

    '''
    app.logger.debug("Spawned thread to follow piaware logs")
    curr_pos = 0
    try:
        while True:
            if client_sid in client_states and client_states[client_sid]['stop_thread']:
                break
            # Open file for reading
            with open('/var/log/piaware.log', 'rb') as f:
                # Seek EOF position
                f.seek(0,2)
                end_pos = f.tell()

                # Skip the current position ahead for the initial read to avoid reading the entire file
                if curr_pos == 0:
                    curr_pos = max(curr_pos, (end_pos - 200*160))

                    # Read forward until next new line in case we land in the middle of a line
                    f.seek(curr_pos)
                    while True:
                        char = f.read(1)
                        curr_pos += 1
                        if not char or char == b'\n':
                            break

                # If EOF is greater than our current position, this indicates new log data.
                # Emit all the new lines up to end of file and update the current_position
                if end_pos > curr_pos:
                    f.seek(curr_pos)
                    for line in f:
                        socketio.emit('log_data', line.decode('utf-8', errors="replace"), room=client_sid)
                        socketio.sleep(0)
                    curr_pos = f.tell()

            # Check for new data every 3 seconds
            socketio.sleep(3)
    except:
        app.logger.error("Error reading piaware.log")
        socketio.emit('log_data', "Error reading piaware.log...", room=client_sid)


def validate_json(request):
    """Validate request to ensure it is json

    Return the json data if valid
    """

    # Check content type
    if not request.is_json:
        response = make_response(jsonify(success=False,
                                 error="content-type must be application/json"),
                                 HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        abort(response)

    try:
        _ = request.data.decode("utf-8")
    except UnicodeDecodeError:
        response = make_response(jsonify(sucess=False,
                                 error="Data must be UTF-8 encoded"),
                                 HTTPStatus.BAD_REQUEST)
        abort(response)

    # Check for valid json
    if not isinstance(request.get_json(silent=True), dict):
        response = make_response(jsonify(sucess=False,
                                 error="Invalid json in request"),
                                 HTTPStatus.BAD_REQUEST)
        abort(response)

    return request.get_json()


def validate_form(request):
    """Validate request to ensure it's application/x-www-form-urlencoded

    Return form data as a dict
    """

    if request.content_type != 'application/x-www-form-urlencoded':
        response = make_response(jsonify(success=False, error="content-type must be application/x-www-form-urlencoded"), HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        abort(response)

    return request.form.to_dict()


def process_json(json_payload):
    """ Process json payload and call approriate piaware-config handler functions

    Returns a Flask Response object
    """

    try:
        request = json_payload['request']
    except KeyError:
        response = make_response(jsonify(success=False, error="Missing request field"), HTTPStatus.BAD_REQUEST)
        abort(response)

    app.logger.info(f'Incoming request: {request}')
    app.logger.debug(f'{json_payload}')
    if request == 'piaware_config_read':
        json_response, status_code = message_handlers.handle_read_config_request(json_payload)
    elif request == 'piaware_config_write':
        json_response, status_code = message_handlers.handle_write_config_request(json_payload)
    elif request == 'get_device_info':
        json_response, status_code = message_handlers.handle_get_device_info_request()
    elif request == 'get_device_state':
        json_response, status_code = message_handlers.handle_get_device_state_request()
    elif request == 'get_network_info':
        json_response, status_code = message_handlers.handle_get_network_info()
    elif request == 'get_wifi_networks':
        json_response, status_code = message_handlers.handle_get_wifi_networks_request()
    elif request == 'set_wifi_config':
        json_response, status_code = message_handlers.handle_set_wifi_config_request(json_payload)
    elif request == 'restart_receiver':
        json_response, status_code = message_handlers.handle_restart_receiver_request()
    elif request == 'restart_network':
        json_response, status_code = message_handlers.handle_restart_network_request()
    elif request == 'reboot':
        json_response, status_code = message_handlers.handle_reboot_request()
    elif request == 'get_pending_network_config':
        json_response, status_code = message_handlers.handle_read_pending_network_config_request(json_payload)
    elif request == 'set_pending_network_config':
        json_response, status_code = message_handlers.handle_write_pending_network_config_request(json_payload)
    elif request == 'save_pending_network_settings':
        json_response, status_code = message_handlers.handle_save_pending_network_settings()
    elif request == 'delete_pending_network_settings':
        json_response, status_code = message_handlers.handle_delete_pending_network_settings()
    else:
        app.logger.error(f'Unrecognized request: {request}')
        json_response, status_code = {"success": False, "error": "Unsupported request"}, HTTPStatus.BAD_REQUEST

    app.logger.debug(f'Response: {json_response}')

    return make_response(jsonify(json_response), status_code)


class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """
    def filter(self, record):
        record.APP_NAME = APP_NAME
        return True


def setup_production_logger():
    """ Set up logger properly when deployed behind Gunicorn WSGI server

    """
    # Get Gunicorn logger
    gunicorn_logger = logging.getLogger('gunicorn.error')

    # Use Gunicorn logger handlers and log level
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    # Modify log message format to include app name
    formatter = logging.Formatter('%(asctime)s - %(APP_NAME)s - [%(levelname)s] - %(message)s')
    filter = ContextFilter()
    app.logger.handlers[0].setFormatter(formatter)
    app.logger.handlers[0].addFilter(filter)
