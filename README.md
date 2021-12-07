# PiAware Configurator
piaware-configurator is a Python web server that can be used to configure PiAware over HTTP. It is currently intended to run on PiAware SD card images to supplement piaware configuration over Bluetooth Low Energy. It will later be extended to provide easier configuration of PiAware.

It is implemented using Flask so you can easily run it using Flask's built-in development server.

In production, it is deployed behind the Python WSGI HTTP Server, [gunicorn](https://gunicorn.org/).

## HTTP Endpoints
**< Host IP >:5000/configurator** - Configurator endpoint

- Takes JSON POST requests to read/write piaware-config settings

## Tohil Usage
piaware-configurator uses [Tohil](https://github.com/flightaware/tohil) to bridge the gap between Python and Tcl and allows configuration of piaware using Python.
