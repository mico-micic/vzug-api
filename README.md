# V-ZUG API Library

**Unofficial** python API library for V-ZUG devices. This module provides an API for communication with V-ZUG devices in a local network. Communication with the central V-ZUG services (V-ZUG-Home) is not supported.

## Implemented functions

* Any V-ZUG device with network support:
  * Get basic status information.
  * Support username / password authentication (not tested yet).

* Washing machines:
  * Get power and water consumption data.
  * Get extended information for running program incl. optiDos status. 

## Limitations and Warning
Since I have only one V-ZUG machine (AdoraWash V4000), the library is not tested with other devices.

## How to use
Check example implementations in [examples/any_device.py](examples/any_device.py) and [examples/washing_machine.py](examples/washing_machine.py).

## How to add new device
Feel free to contribute more devices by ...
* adding a corresponding response-json file in [test/resources](test/resources),
* writing a unit- / integration-test
* and creating a new device class like [washing_machine.py](vzug/washing_machine.py).

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