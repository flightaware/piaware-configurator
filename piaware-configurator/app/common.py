from flask import current_app

piaware_config_read_whitelist = [
    "allow-ble-setup",  "image-type", "flightfeeder-serial", "rtlsdr-gain", "uat-sdr-gain",
    "wireless-network", "wireless-type", "wireless-address", "wireless-ssid", "wireless-netmask", "wireless-gateway", "wireless-country", "wireless-broadcast", "wireless-nameservers",
    "wired-network", "wired-type", "wired-address", "wired-netmask", "wired-gateway", "wired-broadcast", "wired-nameservers"
    ]
piaware_config_write_whitelist = ["allow-ble-setup", "wireless-network", "wireless-type", "wireless-address", "wireless-ssid", "wireless-netmask", "wireless-gateway", "wireless-country", "wireless-broadcast", "wireless-nameservers", "wireless-password",
    "wired-network", "wired-type", "wired-address", "wired-netmask", "wired-gateway", "wired-broadcast", "wired-nameservers", "rtlsdr-gain"]

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