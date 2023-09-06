# PiAware Configurator
piaware-configurator is an API that provides several endpoints to read and write piaware configuration settings and retrieve device information and status over HTTP. It is implemented using [Flask](https://flask.palletsprojects.com/) so you can run it using Flask's built-in development server. In production, it is deployed behind the Python WSGI HTTP Server, [gunicorn](https://gunicorn.org/).

piaware-configurator is bound to localhost which makes it inaccessible to external hosts. Its intended use is for Bluetooth configuration and Web interface for ADS-B receivers.

## Endpoints

**URL**: http://localhost:5000/configurator

**Method**: `POST`

**Requests:** Endpoint accepts JSON formatted requests consisting of a "request" and a "request_payload" key to interface with piaware-config and device information 


| Request | Command | Request Format (must be Content-Type: application/json) | 
| --------------- | --------------- | --------------- |
| Read piaware config setting | piaware_config_read | `{ "request": "piaware_config_read", "request_payload" : ["receiver-type", "rtlsdr-gain"]}` | 
| Set piaware config setting | piaware_config_write | `{"request": "piaware_config_write", "request_payload": {"receiver-type": "rtlsdr", "rtlsdr-gain": 50}}` |
| Get device info | get_device_info | `{"request": "get_device_info"}` | 
| Get network info | get_network_info | `{"request": "get_network_info"}` | 
| Get device state | get_device_state | `{"request": "get_device_state"}` | 
| Get available WiFi networks | get_wifi_networks | `{"request": "get_wifi_networks"}` | 
| Set Wifi configuration | set_wifi_config | `{"request": "set_wifi_config", "request_payload": {"wireless-ssid": <ssid>, "wireless-password": "<password>", "wireless-country": "<countrycode>"}}` | 
| Restart receiver | restart_receiver | `{"request": "restart_receiver"}` |

**Response**: `200 OK`
```
{"success": true, "receiver-type": "rtlsdr", "rtlsdr-gain": 50}
{"success": false, "error": "Reading rtlsdr-gain is not allowed"}
{"success": false, "error": "Badly formatted setting"}
{"success": false, "error": "Server error occurred reading config setting: rtlsdr-gain"}
```

**Response**: `400 BAD REQUEST`
```
{"success": False, "error": "Missing request_payload field"}
{"success": False, "error": "Request_payload must be a list of settings to read"}
```

___
**URL**: http://localhost:5000/piaware/status

Returns the piaware status JSON

**Method**: `GET`

**Supported Responses**: 

`200 OK`
```
{
    "modes_enabled"    : true,
    "dump978_version"  : "dump978-fa 8.2",
    "interval"         : 5000,
    "cpu_load_percent" : 6,
    "time"             : 1693969799444,
    "site_url"         : "https://flightaware.com/adsb/stats/user/piawareuser
    "system_uptime"    : 342330,
    "expiry"           : 1693969810444,
    "piaware"          : {
        "status"  : "green",
        "message" : "PiAware 8.2 is running"
    },
    "cpu_temp_celcius" : 55.017,
    "uat_enabled"      : false,
    "dump1090_version" : "dump1090-fa 8.2",
    "adept"            : {
        "status"  : "green",
        "message" : "Connected to FlightAware and logged in"
    },
    "mlat"             : {
        "status"  : "amber",
        "message" : "No clock synchronization with nearby receivers"
    },
    "piaware_version"  : "8.2",
    "radio"            : {
        "status"  : "green",
        "message" : "Received Mode S data recently"
    }
}
```

`404 NOT FOUND` - No piaware status.json exists

___ 
**URL**: http://localhost:5000/flightfeeder/status

Returns the flightfeeder status JSON

**Method**: `GET`

**Supported Responses**: 

`200 OK`
```
{
    "serial"           : "10508",
    "software_version" : "11.0",
    "modes_enabled"    : true,
    "type"             : "flightfeeder",
    "interval"         : 60000,
    "cpu_load_percent" : 9,
    "site_url"         : "https://flightaware.com/adsb/stats/user/flightfeederuser",
    "time"             : 1693969878283,
    "system_uptime"    : 372924,
    "expiry"           : 1693970059283,
    "piaware"          : {
        "status"  : "green",
        "message" : "PiAware 8.2 is running; piaware running with pid 648"
    },
    "mac"              : "b8:27:eb:d1:f1:e8",
    "network"          : {
        "status"  : "green",
        "message" : "Remote management VPN connected"
    },
    "hardware_version" : "FlightFeeder Orange",
    "cpu_temp_celcius" : 50.464,
    "uat_enabled"      : false,
    "adept"            : {
        "status"  : "green",
        "message" : "Connected to FlightAware and logged in"
    },
    "mlat"             : {
        "status"  : "green",
        "message" : "Multilateration synchronized"
    },
    "radio"            : {
        "status"  : "green",
        "message" : "Received Mode S data recently"
    }
}
```

`404 NOT FOUND` - No FlightFeeder status.json exists

## Tohil Usage
piaware-configurator uses [Tohil](https://github.com/flightaware/tohil) to bridge the gap between Python and Tcl and allows configuration of piaware using Python.
