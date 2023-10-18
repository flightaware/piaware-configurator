from flask import current_app
from http import HTTPStatus
import json
import os
import subprocess

from .piaware_config_helpers import *
from .flightfeeder_config_helpers import get_pending_network_config, set_pending_network_config
from .wifi_helpers import get_wifi_networks, scan_wifi_networks, parse_wifi_networks

API_VERSION = '2.0.0'


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

def handle_read_pending_network_config_request(config_request):
    """ Read pending network configuration setting

        Expected config_request format:
        {
            "request": "get_pending_network_config",
            "request_payload" : ["wireless-network", "wireless-ssid"]
        }

        request_payload must be a list of config settings to read
    """
    filename = "/run/flightfeeder-volatile-config.txt"

    if not os.path.exists(filename):
        return {"success": False, "error": "No pending settings exist"}, 404

    try:
        read_settings = config_request['request_payload']
        if type(read_settings) is not list:
            raise TypeError

        response = {}
        for config in read_settings:
            value = get_pending_network_config(config)
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

def handle_write_pending_network_config_request(config_request):
    """ Set pending network configuration settings.

        Expected config_request format:
        {
            "request": "set_pending_network_config",
            "request_payload" : {"wireless-ssid": "MyWifiNetwork", "wireless-address": "192.168.0.111"}
        }

        request_payload must be a dictionary of key/value configuration setting pairs
    """
    filename = "/run/flightfeeder-volatile-config.txt"

    # If volatile config file doesn't exist, create it
    if not os.path.exists(filename):
        cmd = ["sudo", "touch", filename]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        write_settings = config_request['request_payload']
        if type(write_settings) is not dict:
            raise TypeError

        updated_settings = {}
        for config, value in write_settings.items():
            set_pending_network_config(config, value)
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
    try:
        image_type = get_piaware_config('image-type')
        json_response['image_type'] = image_type
        if image_type.startswith('flightfeeder'):
            flightfeeder_serial_number = get_piaware_config('flightfeeder-serial')
            json_response['flightfeeder_serial'] = flightfeeder_serial_number
        json_response['success'] = True
    except Exception as e:
        current_app.logger.error(f'Error getting device info: {e}')
        json_response['success'] = False
        json_response['error'] = "Error obtaining full device information"

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

        device_location = get_device_location()
        unique_feeder_id = get_unique_feederid()

        is_claimed = False
        is_connected_to_FA = None
        site_id = None

        flightfeeder_status_file = '/var/run/flightfeeder/status.json'
        piaware_status_file = '/var/run/piaware/status.json'

        if os.path.exists(flightfeeder_status_file):
            with open(flightfeeder_status_file) as f:
                status_json = json.load(f)
            is_claimed = True
        elif os.path.exists(piaware_status_file):
            with open(piaware_status_file) as f:
                status_json = json.load(f)
            is_claimed = bool(unique_feeder_id) and is_receiver_claimed(status_json)

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
                        'network_interface': interface,
                        'device_location': device_location
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

def handle_get_network_info():
    """ Returns current network status and configuration

    """
    try:
        # wireless network piaware-config settings
        wireless_network = get_piaware_config('wireless-network')
        wireless_type = get_piaware_config('wireless-type')
        wireless_address = get_piaware_config('wireless-address')
        wireless_netmask = get_piaware_config('wireless-netmask')
        wireless_gateway = get_piaware_config('wireless-gateway')
        wireless_broadcast = get_piaware_config('wireless-broadcast')
        wireless_nameservers = get_piaware_config('wireless-nameservers')
        wireless_country = get_piaware_config('wireless-country')
        wireless_ssid = get_piaware_config('wireless-ssid')

        # wired network piaware-config settings
        wired_network = get_piaware_config('wired-network')
        wired_type = get_piaware_config('wired-type')
        wired_address = get_piaware_config('wired-address')
        wired_netmask = get_piaware_config('wired-netmask')
        wired_gateway = get_piaware_config('wired-gateway')
        wired_broadcast = get_piaware_config('wired-broadcast')
        wired_nameservers = get_piaware_config('wired-nameservers')

        # IP address and ethernet/wifi state
        eth0_ipaddress = tohil.eval('::fa_sysinfo::interface_ip_address eth0', to=str)
        wlan_interface = tohil.eval('::fa_sysinfo::wireless_interface', to=str)
        wlan_ipaddress = tohil.eval(f'::fa_sysinfo::interface_ip_address {wlan_interface}', to=str)
        ethernet_state = tohil.eval('::fa_sysinfo::interface_state eth0', to=str)
        wifi_state = tohil.eval(f'::fa_sysinfo::interface_state {wlan_interface}', to=str)

        json_response = {'wireless-network': wireless_network,
                        'wireless-type': wireless_type,
                        'wireless-address': wireless_address,
                        'wireless-netmask': wireless_netmask,
                        'wireless-gateway': wireless_gateway,
                        'wireless-broadcast': wireless_broadcast,
                        'wireless-nameservers': wireless_nameservers,
                        'wireless-country': wireless_country,
                        'wireless-ssid': wireless_ssid,
                        'wlan-ipaddress': wlan_ipaddress,
                        'wired-network': wired_network,
                        'wired-type': wired_type,
                        'wired-address': wired_address,
                        'wired-netmask': wired_netmask,
                        'wired-gateway': wired_gateway,
                        'wired-broadcast': wired_broadcast,
                        'wired-nameservers': wired_nameservers,
                        'eth0-ipaddress': eth0_ipaddress,
                        'wifi-state': wifi_state,
                        'ethernet-state': ethernet_state
                        }

        status_code = HTTPStatus.OK
    except PiAwareConfigException as e:
        error = f"Server error occurred reading wireless setting: {e.setting}"
        json_response, status_code = {"success": False, "error": error}, HTTPStatus.OK
    except Exception as e:
        current_app.logger.error(f'Error getting device state: {e}')
        json_response, status_code = {"success": False, "error": "Server error occurred retrieving device settings"}, HTTPStatus.OK

    return json_response, status_code

def handle_restart_receiver_request():
    current_app.logger.info(f'Restarting receiver...')
    try:
        tohil.eval('::fa_sudo::popen_as -root -- /usr/bin/piaware-restart-receiver')
        json_response, status_code = {"success": True}, HTTPStatus.OK
    except subprocess.CalledProcessError:
        json_response, status_code = {"success": False, "error": "Error restarting receiver"}, HTTPStatus.OK
    except Exception:
        json_response, status_code = {"success": False, "error": "Server error restarting receiver"}, HTTPStatus.OK

    return json_response, status_code


def handle_restart_network_request():
    current_app.logger.info(f'Restarting network...')
    try:
        tohil.eval('::fa_sudo::popen_as -root -- /usr/bin/piaware-restart-network')
        json_response, status_code = {"success": True}, HTTPStatus.OK
    except subprocess.CalledProcessError:
        json_response, status_code = {"success": False, "error": "Error restarting network"}, HTTPStatus.OK
    except Exception:
        json_response, status_code = {"success": False, "error": "Server error restarting network"}, HTTPStatus.OK

    return json_response, status_code

def handle_reboot_request():
    current_app.logger.info(f'Rebooting device...')
    try:
        tohil.eval('::fa_sudo::exec_as -root -- /sbin/shutdown -r now')
    except subprocess.CalledProcessError:
        json_response, status_code = {"success": False, "error": "Error rebooting device"}, HTTPStatus.OK
    except Exception:
        json_response, status_code = {"success": False, "error": "Server error occurred"}, HTTPStatus.OK

    return json_response, status_code

def handle_save_pending_network_settings():
    ''' Handler function to save the volatile config settings permanently

        This function will write the pending settings to piaware config and remove
        the volatile config file.
    '''
    # Read the flightfeeder volatile config settings
    filename = "/run/flightfeeder-volatile-config.txt"
    if not os.path.exists(filename):
        # Return 404 if no pending settings exist
        return {"success": False, "error": "No pending settings exist"}, 404

    # Store the config settings in memory so we can save them permanently
    config_dict = {}
    with open(filename) as f:
        for line in f:
            fields = line.split()
            config, value = fields[0], fields[1]
            config_dict[config] = value

    # Remove the flightfeeder-volatile-config.txt file first, otherwise
    # any piaware-config setting will just update this file
    cmd = ["sudo", "rm", filename]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Save settings permanently by writing them to piaware-config
    for k,v in config_dict.items():
        set_piaware_config(k, v)

    return {"success": True}, 200