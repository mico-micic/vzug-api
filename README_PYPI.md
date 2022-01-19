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

## Limitations and Warning
Since we ([Darko Micic](https://github.com/dmicic) and me) have only two V-ZUG machines (AdoraWash and AdoraDry V4000), the library is not tested with other devices.

## How to use
Check [examples (github.com)](https://github.com/mico-micic/vzug-api/tree/main/examples) directory for implementations.