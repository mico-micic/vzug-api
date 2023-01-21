# V-ZUG API Library

**Unofficial** python API library for V-ZUG devices. This module provides an API for communication with V-ZUG devices in a local network. Communication with the central V-ZUG services (V-ZUG-Home) is not supported.

## Implemented functions

* Any V-ZUG device with network support:
  * Get basic status information.
  * Support username / password authentication.

* Washing machines:
  * Get power and water consumption data.
  * Get extended information for running program incl. optiDos status. 

* Dryers:
  * Get power consumption data.
  * Get extended information for running program. 

* Dishwashers:
  * Get extended information for running / timed program. 

## Limitations and Warning
Since we ([Darko Micic](https://github.com/dmicic) and me) have only two V-ZUG machines (AdoraWash and AdoraDry V4000), the library is not tested with other devices.

## How to use
Check example implementations in [examples/any_device.py](examples/any_device.py) and [examples/washing_machine.py](examples/washing_machine.py).

### Home Assistant Integration
This API is used for the [Home Assistant](https://www.home-assistant.io/) V-ZUG integration (unofficial): [/feature/vzug-integration](https://github.com/mico-micic/core/tree/feature/vzug-integration) (currently under development)

## How to Develop / Contribute
To set up the development environment:

1. Checkout this repository,
2. Create virtual environment ([python venv](https://docs.python.org/3/library/venv.html)),
3. Run [devtools/install-dev-deps.sh](devtools/install-dev-deps.sh) or (if you don't have bash) run the pip install lines from the [install-dev-deps.sh](devtools/install-dev-deps.sh) file manually.
4. Run `pip install -e .` 

## How to add new device
Feel free to contribute more devices by ...
* adding a corresponding response-json file in [test/resources](test/resources),
* writing a unit- / integration-test,
* creating a new device class like [washing_machine.py](vzug/washing_machine.py).

Or
* just send me a response-json, so I can implement the tests and device class (at least a first version).

## What is a response-json file?
A response-json file contains the response got from the device when calling a specific REST Endpoint. Example response received when calling the `/ai?command=getDevceStatus` endpoint: 

```json
{
  "DeviceName": "TestDevice",
  "Serial": "123",
  "Inactive": "false",
  "Program": "TestProgram",
  "Status": "Testing",
  "ProgramEnd": {
    "End": "",
    "EndType": "0"
  },
  "deviceUuid": "test-uuid"
}
```
Source: [device_status_ok_resp.json](test/resources/device_status_ok_resp.json)

## How to get a response-json file?
Open the http web interface of the device while the browser developer tools are open. In the developer tools "network" tab check the communication and copy the device response (JSON) into a textfile. 