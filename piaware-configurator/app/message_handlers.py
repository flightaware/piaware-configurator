from flask import current_app
from http import HTTPStatus
import subprocess

from .piaware_config_helpers import *
from .wifi_helpers import get_wifi_networks, scan_wifi_networks, parse_wifi_networks

API_VERSION = '1.0.0'


def handle_read_config_request(config_request):
    """Read piaware-config setting

        Expected config_request format:
        {
            "request": piaware_config_read
            "request_payload" : ["rtlsdr-gain"]
        }

        request_payload must be a list of config settings to read
    """
    try:
        read_settings = config_request['request_payload']
        if type(read_settings) is not list:
            raise TypeError

        response = {}
        for config in read_settings:
            value = get_piaware_config(config)
            response[config] = value

        response["success"] = True
        json_response, status_code = response, HTTPStatus.OK
    except KeyError:
        json_response, status_code = {"success": False, "error": "Missing request_payload field"}, HTTPStatus.BAD_REQUEST
    except TypeError:
        json_response, status_code = {"success": False, "error": "Request_payload must be a list of settings to read"}, HTTPStatus.BAD_REQUEST
    except PiAwareConfigPermissionException as e:
        error = f"Reading {e.setting} is not allowed"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except PiAwareConfigAsciiStringException as e:
        error = f"Badly formatted setting"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except PiAwareConfigException as e:
        error = f"Server error occurred reading config setting: {e.setting}"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK

    return json_response, status_code


def handle_write_config_request(config_request):
    """Set piaware-config setting

        Expected config_request format:
        {
            "request": piaware_config_write
            "request_payload" : {"rtlsdr-gain": 20, "wireless-network": "no"}
        }

        request_payload must be a dictionary of key/value configuration setting pairs
    """
    try:
        write_settings = config_request['request_payload']
        if type(write_settings) is not dict:
            raise TypeError

        updated_settings = {}
        for config, value in write_settings.items():
            set_piaware_config(config, value)
            updated_settings[config] = value

        json_response, status_code = updated_settings, HTTPStatus.OK
        json_response["success"] = True
    except KeyError:
        json_response, status_code = {"success": False, "error": "Missing request_payload field"}, HTTPStatus.BAD_REQUEST
    except TypeError:
        json_response, status_code = {"success": False, "error": "request_payload must be a dict"}, HTTPStatus.BAD_REQUEST
    except PiAwareConfigPermissionException as e:
        error = f"Setting {e.setting} is not allowed"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except PiAwareConfigAsciiStringException as e:
        error = f"Badly formatted setting"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except PiAwareConfigException as e:
        error = f"Server error occurred writing config setting: {e.setting}"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK

    return json_response, status_code


def handle_get_device_info_request():
    """ Returns piaware-configurator API version

    """
    json_response = {'api_version': API_VERSION}
    status_code = HTTPStatus.OK

    return json_response, status_code


def handle_get_device_state_request():
    """ Returns a dictionary of device settings

    """
    try:
        # read piaware-config settings for wifi credentials
        wireless_ssid = get_piaware_config('wireless-ssid')
        wireless_country = get_piaware_config('wireless-country')
        # Hardcoded for now since we removed read permissions for wireless-password. Unused by clients but
        # still need the key present for this API version
        wireless_password_set = True

        # Check route to FlightAware and IP address via fa_sysinfo pakage and tohil
        route_to_flightaware, ip_address, interface = get_network_state_and_ip()
        is_connected_to_internet = True if route_to_flightaware and not ip_address.startswith("169.254") else False

        unique_feeder_id = get_unique_feederid()

        with open('/var/run/piaware/status.json') as f:
            status_json = json.load(f)

        # read info from local files (status.json & feeder_id)
        is_claimed = True if unique_feeder_id != "" and is_receiver_claimed(status_json) else False
        is_connected_to_FA = is_connected_to_flightaware(status_json)
        site_id = get_adsb_site_number(status_json)

        json_response = {'wireless-country': wireless_country,
                        'wireless-ssid': wireless_ssid,
                        'wireless-ip': ip_address,
                        'is_connected_to_internet': is_connected_to_internet,
                        'is_password_set': wireless_password_set,
                        'is_receiver_claimed': is_claimed,
                        'is_connected_to_FA': is_connected_to_FA,
                        'feeder_id': unique_feeder_id,
                        'site_id': site_id,
                        'network_interface': interface
                        }
        status_code = HTTPStatus.OK

    except PiAwareConfigException as e:
        error = f"Server error occurred reading wireless setting: {e.setting}"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except Exception as e:
        current_app.logger.error(f'Error getting device state: {e}')
        json_response, status_code = {"success": False, "error": "Server error occurred retrieving device settings"}, HTTPStatus.OK

    return json_response, status_code


def handle_get_wifi_networks_request():
    """Returns a dictionary of visible wireless networks and relevant information

    Example return data:
    {
        "wifi_networks": [
        {
            "ssid": "MyWifiNetwork",
            "encrypted": True,
            "is_5Ghz": False,
            "signal": -68,
            "wifi_cell": "01"
        },
        {
            "ssid": "MyWifiNetwork_5G",
            "encrypted": True,
            "is_5Ghz": True,
            "signal": -40,
            "wifi_cell": "02"
        }]
    }
    """
    try:
        current_app.logger.debug(f'Getting wifi networks...')
        iw_list_data = get_wifi_networks()

        # Do an actual scan if something went wrong getting it from wifi_scan script
        if iw_list_data == "":
            current_app.logger.info(f'Scanning for wifi networks...')
            iw_list_data = scan_wifi_networks()

        wifi_networks = {}
        wifi_networks['wifi_networks'] = parse_wifi_networks(iw_list_data)

        json_response, status_code = wifi_networks, HTTPStatus.OK
    except Exception as e:
        current_app.logger.error(f'Error getting wifi networks: {e}')
        json_response, status_code = {"success": False, "error": "Server error getting wifi networks"}, HTTPStatus.OK

    return json_response, status_code


def handle_set_wifi_config_request(config_request):
    """Sets wireless piaware-config settings and invokes the piaware-restart-network
       restarts network command to apply changes

    Expected config_request format:
    {
        "request_payload": {
            "wireless-ssid": <ssid>,
            "wireless-password": "<password>",
            "wireless-country": "<countrycode>"
        }
    }

    """
    try:
        wifi_credentials = config_request['request_payload']

        if type(wifi_credentials) is not dict:
            raise TypeError

        for config, value in wifi_credentials.items():
            set_piaware_config(config, value)

        if "requestor" in config_request and config_request["requestor"] == "piaware-ble-connect":
           current_app.logger.info(f'Setting WiFi configuration over Bluetooth. Setting allow-ble-setup to "yes".')
           set_piaware_config("allow-ble-setup", "yes")

        current_app.logger.info(f'Restarting network...')
        tohil.eval('::fa_sudo::popen_as -root -- /usr/bin/piaware-restart-network')

        json_response, status_code = {"success": True}, HTTPStatus.OK
    except KeyError:
        json_response, status_code = {"success": False, "error": "Missing payload in request"}, HTTPStatus.BAD_REQUEST
    except TypeError:
        json_response, status_code = {"success": False, "error": "Invalid JSON format"}, HTTPStatus.BAD_REQUEST
    except subprocess.CalledProcessError:
        json_response, status_code = {"success": False, "error": "Error restarting network"}, HTTPStatus.OK
    except Exception:
        json_response, status_code = {"success": False, "error": "Server error writing config setting"}, HTTPStatus.OK

    return json_response, status_code
