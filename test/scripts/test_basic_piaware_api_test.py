import requests
import unittest
import pytest

@pytest.mark.usefixtures("get_base_url")
class TestBasicPiawareApi:

    def test_api_get_device_info(self, get_base_url):
        payload = {"request": "get_device_info"}
        resp = requests.post(get_base_url + "configurator", json=payload)
        assert resp.status_code == 200, "Status code is not 200. Rather found : " + str(
            resp.status_code
        )
        data = resp.json()
        expected_device_info_res = [
            "api_version",
            "flightfeeder_serial",
            "image_type",
            "success",
        ]
        assert len(list(data.keys())) == len(expected_device_info_res) and sorted(
            list(data.keys())
        ) == sorted(expected_device_info_res)
        assert data["success"] == True, "success key value is not true"
        assert (
            data["image_type"] == "flightfeeder-combined"
        ), "Image type is not flightfeeder combined"
        assert data["api_version"] != "", "API version is empty"
        assert data["flightfeeder_serial"] != "", "FlighFeeder serial is empty"

    def test_api_get_device_state(self, get_base_url):
        payload = {"request": "get_device_state"}
        resp = requests.post(get_base_url + "configurator", json=payload)
        assert resp.status_code == 200, "Status code is not 200. Rather found : " + str(
            resp.status_code
        )
        actual_device_state = resp.json()
        expected_device_state_res = [
            "device_location",
            "feeder_id",
            "is_connected_to_FA",
            "is_connected_to_internet",
            "is_password_set",
            "is_receiver_claimed",
            "network_interface",
            "site_id",
            "wireless-country",
            "wireless-ip",
            "wireless-ssid",
        ]
        assert (
            actual_device_state["wireless-ip"] == "172.16.32.89"
        ), "wireless ip has changed"
        assert (
            actual_device_state["wireless-ssid"] == "FlightAware"
        ), "wireless-ssid has changed"
        assert isinstance(
            actual_device_state["device_location"], list
        ), "'device_location' value is not a list"
        assert len(list(actual_device_state.keys())) == len(expected_device_state_res)
        assert sorted(list(actual_device_state.keys())) == sorted(
            expected_device_state_res
        )
     
    def test_api_get_wifi_networks(self, get_base_url):
        payload = {"request": "get_wifi_networks"}
        resp = requests.post(get_base_url + "configurator", json=payload)
        assert resp.status_code == 200, "Status code is not 200. Rather found : " + str(
            resp.status_code
        )
        data = resp.json()
        expected_wifi_network_res = [
            "encrypted",
            "is_5Ghz",
            "signal",
            "wifi_cell",
            "wireless-ssid",
        ]
        assert len(list(data["wifi_networks"][0].keys())) == len(
            expected_wifi_network_res
        ) and sorted(list(data["wifi_networks"][0].keys())) == sorted(
            expected_wifi_network_res
        )
        assert len(list(data["wifi_networks"][0].keys())) == len(expected_wifi_network_res)
        assert sorted(list(data["wifi_networks"][0].keys())) == sorted(
            expected_wifi_network_res
        )
        assert isinstance(
            data["wifi_networks"], list
        ), "'wifi networks' value is not a list"
