import requests
import pytest


@pytest.mark.usefixtures("get_base_url")
class TestPiawareReadWriteConfig:
    def test_api_read_piaware_config(self, get_base_url):
        piaware_config_read_whitelist = [
            "allow-ble-setup",
            "image-type",
            "flightfeeder-serial",
            "rtlsdr-gain",
            "uat-sdr-gain",
            "wireless-network",
            "wireless-type",
            "wireless-address",
            "wireless-ssid",
            "wireless-netmask",
            "wireless-gateway",
            "wireless-country",
            "wireless-broadcast",
            "wireless-nameservers",
            "wired-network",
            "wired-type",
            "wired-address",
            "wired-netmask",
            "wired-gateway",
            "wired-broadcast",
            "wired-nameservers",
        ]
        for config in piaware_config_read_whitelist:
            req_list = []
            req_list.append(config)
            payload = {"request": "piaware_config_read", "request_payload": req_list}
            resp = requests.post(get_base_url + "configurator", json=payload)
            assert (
                resp.status_code == 200
            ), "Status code is not 200. Rather found : " + str(resp.status_code)
            data = resp.json()
            assert data["success"] == True, "success key value is not true"
            assert config in data.keys(), "{} value is not returned in response".format(
                config
            )
