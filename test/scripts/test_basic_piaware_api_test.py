import requests
import unittest

BASE_URL= "http://172.16.32.89:3000/"

class TestBasicPiawareApi(unittest.TestCase):
    def test_api_get_device_info(self):
        payload={"request": "get_device_info"}
        resp = requests.post(url=BASE_URL+"configurator", json=payload)
        assert (resp.status_code == 200), "Status code is not 200. Rather found : " + str(resp.status_code)
        data = resp.json()
        expected_device_info_res = ['api_version', 'flightfeeder_serial', 'image_type', 'success']
        self.assertListEqual(list(data.keys()), expected_device_info_res)
        assert data["success"] == True, "success key value is not true"
        assert data["image_type"] == 'flightfeeder-combined', "Image type is not flightfeeder combined"
        assert data["api_version"] != '', "API version is empty"
        assert data["flightfeeder_serial"] != '', "FlighFeeder serial is empty"


    def test_api_get_device_state(self):
        payload={"request": "get_device_state"}
        resp = requests.post(url=BASE_URL+"configurator", json=payload)
        assert (resp.status_code == 200), "Status code is not 200. Rather found : " + str(resp.status_code)
        data = resp.json()
        expected_device_state_res = ['device_location', 'feeder_id', 'is_connected_to_FA', 'is_connected_to_internet', 'is_password_set', 'is_receiver_claimed','network_interface','site_id','wireless-country','wireless-ip','wireless-ssid']
        self.assertListEqual(list(data.keys()), expected_device_state_res)
        assert isinstance(data["device_location"], list), "'device_location' value is not a list"
        assert data['wireless-ip'] == '172.16.32.89', 'wireless ip has changed'
        assert data['wireless-ssid'] == 'FlightAware', 'wireless-ssid has changed'

    def test_api_get_wifi_networks(self):
        payload={"request": "get_wifi_networks"}
        resp = requests.post(url=BASE_URL+"configurator", json=payload)
        assert (resp.status_code == 200), "Status code is not 200. Rather found : " + str(resp.status_code)
        data = resp.json()
        expected_wifi_network_res = ['encrypted', 'is_5Ghz', 'signal', 'wifi_cell', 'wireless-ssid']
        self.assertListEqual(list(data['wifi_networks'][0].keys()), expected_wifi_network_res)
        assert isinstance(data["wifi_networks"], list), "'wifi networks' value is not a list"
       