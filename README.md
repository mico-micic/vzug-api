# V-ZUG API Library

**Unofficial** python API library for V-ZUG devices. This module provides an API for communication with V-ZUG devices in a local network. Communication with the central V-ZUG services (V-ZUG-Home) is not supported.

## Implemented functions

* Any V-ZUG device with network support:
  * Get basic status information.
  * Support username / password authentication.

* Washing machines:
  * Get extended device information like energy and water consumption.
  * Get extended information for running programs incl. optiDos status. 

## Limitations and Warning:
Since I only have one V-ZUG machine (an AdoraWash V4000), the library is not really tested with other devices.

## How to add new device:
Feel free to contribute more devices by ...
* adding a corresponding response-json file in [test/resources](test/resources),
* writing a unit / integration test
* and creating a new device class like [washing_machine.py](vzug/washing_machine.py).

Or
* just send me a response-json and I will implement the tests and device class (at least a first version).

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
Open the web interface of the device while the developer tools are open in the browser. In the "network" tab check the communication and copy the device response (JSON) into a textfile. 