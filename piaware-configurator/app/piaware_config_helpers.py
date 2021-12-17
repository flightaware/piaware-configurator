from flask import current_app
import tohil
import json

piaware_config_read_whitelist = ["allow-ble-setup", "wireless-network", "wireless-ssid", "wireless-country"]
piaware_config_write_whitelist = ["allow-ble-setup", "wireless-network", "wireless-ssid", "wireless-password", "wireless-country"]

class PiAwareConfigException(Exception):
    def __init__(self, setting):
        self.setting = setting

class PiAwareConfigPermissionException(PiAwareConfigException):
    def __init__(self, setting):
        super().__init__(setting)
        current_app.logger.error(f'Invalid permissions to read {setting}')

class PiAwareConfigAsciiStringException(PiAwareConfigException):
    def __init__(self, setting):
        super().__init__(setting)
        current_app.logger.error(f'Not a valid ASCII string')

def get_piaware_config(setting):
    """ Getter function for piaware-config settings

    """
    if not setting.isascii():
       raise PiAwareConfigAsciiStringException(setting)

    if setting not in piaware_config_read_whitelist:
       raise PiAwareConfigPermissionException(setting)

    try:
        tohil.eval('piawareConfig read_config')
        value = str(tohil.call('piawareConfig', 'get', setting))
    except Exception:
        current_app.logger.error(f'Error reading {setting}. Make sure {setting} is a valid piaware-config option.')
        raise PiAwareConfigException(setting)

    return value


def set_piaware_config(setting, value):
    """ Setter function for piaware-config settings

    """
    if not setting.isascii():
       raise PiAwareConfigAsciiStringException(setting)

    if setting not in piaware_config_write_whitelist:
        raise PiAwareConfigPermissionException(setting)

    try:
        tohil.eval('piawareConfig read_config')
        tohil.call('piawareConfig', 'set_option', setting, value)
        tohil.eval('piawareConfig write_config')
    except Exception:
        current_app.logger.error(f'Error setting {setting} to {value}. Make sure {setting} is a valid piaware-config option.')
        raise PiAwareConfigException(setting)

    return


def get_network_state_and_ip():
    """ Get the network state by checking if there is a route to FlightAware. Return state and current IP address

    """
    try:
        route = tohil.eval('::fa_sysinfo::route_to_flightaware gateway iface ip', to=int)
        if route:
            route_to_flightaware = True
            ip_address = tohil.getvar('ip', to=str)
            interface = tohil.getvar('iface', to=str)
        else:
            route_to_flightaware = False
            ip_address = ""
            interface = ""
    except Exception:
        raise

    return route_to_flightaware, ip_address, interface


def is_receiver_claimed(status_json):
    """ Reads in a valid status.json and returns whether the feeder-id is claimed
        Returns False if cannot be determined.

    """
    if type(status_json) is not dict:
        current_app.logger.error(f'Invalid status_json format received trying to determine if receiver is claimed.')
        return False

    if "unclaimed_feeder_id" not in status_json:
        return True

    return False

def is_connected_to_flightaware(status_json):
    """ Reads in a valid status.json and  returns whether the receiver is currently connected to FlightAware
        Returns False if cannot be determined.

    """
    if type(status_json) is not dict:
        current_app.logger.error(f'Invalid status_json format received trying \
                                   to determine if receiver is connected to FlightAware.')
        return False

    try:
        adept_status = status_json['adept']['status']
        if adept_status == "green":
            return True
    except KeyError:
        current_app.logger.error(f'Error retrieving fa_adept connection status')

    return False


def get_adsb_site_number(status_json):
    """ Reads in a valid status.json for the receiver FA Site ID
        Returns empty string if not found.

    """
    if type(status_json) is not dict:
        current_app.logger.error(f'Invalid status_json format received trying \
                                   to retrieve FA ADS-B Site number.')
        return ""

    try:
        site_url = status_json['site_url']
        if "#stats-" in site_url:
            split_site_url = site_url.split("#stats-")
        elif "/stats/site/" in site_url:
            split_site_url = site_url.split("/stats/site/")
        else:
            return ""

        site_id = split_site_url[1]
        return site_id

    except Exception:
        current_app.logger.debug(f'Could not retrieve Site ID from status.json. May not exist yet.')

    return ""


def get_unique_feederid():
    """ Opens and reads /var/cache/piaware/feeder_id for FA Unique Identifier.
        Returns empty string if not found.

    """
    try:
        with open('/var/cache/piaware/feeder_id') as f:
            feeder_id = f.read().strip()
            return feeder_id
    except Exception:
        current_app.logger.debug(f'Error retrieving Unique Feeder ID')

    return ""
