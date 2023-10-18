from flask import current_app
import tohil
from .common import *

def get_pending_network_config(setting):
    """ Getter function for pending network settings

    """
    if not setting.isascii():
       raise PiAwareConfigAsciiStringException(setting)

    if setting not in piaware_config_read_whitelist:
       raise PiAwareConfigPermissionException(setting)

    try:
        tohil.eval('flightfeederNetworkConfig read_config')
        value = str(tohil.call('flightfeederNetworkConfig', 'get', setting))
    except Exception:
        current_app.logger.error(f'Error reading {setting} from pending network configuration')
        raise PiAwareConfigException(setting)

    return value

def set_pending_network_config(setting, value):
    """ Setter function for pending network settings

    """
    if not setting.isascii():
       raise PiAwareConfigAsciiStringException(setting)

    if setting not in piaware_config_write_whitelist:
        raise PiAwareConfigPermissionException(setting)

    try:
        tohil.eval('flightfeederNetworkConfig read_config')
        tohil.call('flightfeederNetworkConfig', 'set_option', setting, value)
        tohil.eval('flightfeederNetworkConfig write_config')
    except Exception:
        current_app.logger.error(f'Error setting {setting} to {value} in pending network configuration.')
        raise PiAwareConfigException(setting)

    return