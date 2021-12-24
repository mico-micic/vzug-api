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
Check [examples/](https://github.com/mico-micic/vzug-api/tree/main/examples) directory for implementations.