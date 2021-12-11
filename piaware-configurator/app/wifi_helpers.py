from flask import current_app
import subprocess
import re

cell_regex = re.compile(r"^Cell ([\d.]+)")
ssid_regex = re.compile(r"^ESSID:\"(.*)\"$")
frequency_regex = re.compile(r"^Frequency:([\d.]+)")
encrypted_regex = re.compile(r"^Encryption key:(.*)$")
signal_regex = re.compile(r"^Quality=(\d+)\/(\d+)\s+Signal level=(.+) d.+$")


def scan_wifi_networks(interface='wlan0'):
    """ Scan for wifi networks using iwlist and return response

    """
    cmd = ["sudo", "iwlist", interface, "scan"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wifi_network_results = proc.stdout.read().decode('utf-8')
    return wifi_network_results


def get_wifi_networks(interface='wlan0'):
    """ Get available wifi networks created by wifi_scan helper script

    """
    wifi_network_results = ""
    try:
        with open ('/var/run/piaware-configurator/available_wifi_networks') as f:
            wifi_network_results = f.read()
    except Exception as e:
        current_app.logger.error(f'Error getting available wifi networks: {e}')

    return wifi_network_results


def parse_wifi_networks(data):
    """ Parse iwlist output for wifi SSID, Frequency, Encryption, and Signal Strength
        using regex.

    """
    network_array = []
    lines = data.split('\n')
    for line in lines:
        line = line.strip()
        cell_match = cell_regex.search(line)
        if cell_match:
            network_array.append({'wifi_cell': cell_match.group(1)})
            continue

        ssid_match = ssid_regex.search(line)
        if ssid_match:
            wireless_ssid = ssid_match.group(1)
            network_array[-1].update({'wireless-ssid': wireless_ssid})
            continue

        frequency_match = frequency_regex.search(line)
        if frequency_match:
            frequency = frequency_match.group(1)
            is_5Ghz = True if frequency[0] == '5' else False
            network_array[-1].update({'is_5Ghz': is_5Ghz})
            continue

        encrypted_match = encrypted_regex.search(line)
        if encrypted_match:
            encrypted = True if encrypted_match.group(1) == 'on' else False
            network_array[-1].update({'encrypted': encrypted})
            continue

        signal_match = signal_regex.search(line)
        if signal_match:
            signal_level = signal_match.group(3)
            network_array[-1].update({'signal': signal_level})
            continue

    # Return only non-duplicate wifi ssids that are valid and not hidden/empty
    wifi_networks, wifi_network_set = [], []
    for network in network_array:
        if network.get('wireless-ssid') and network['wireless-ssid'] and network['wireless-ssid'][0:4] != "\\x00" and network['wireless-ssid'] not in wifi_network_set:
            wifi_networks.append(network)
            wifi_network_set.append(network['wireless-ssid'])

    return sorted(wifi_networks, key=lambda k: k['signal'])
