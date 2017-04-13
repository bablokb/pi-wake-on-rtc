#!/bin/bash
# --------------------------------------------------------------------------
# Sample command to query next boot time.
#
# This will just return now + 5 minutes
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-wake-on-rtc
#
# --------------------------------------------------------------------------

date -d "now + 5 minutes" +"%Y-%m-%d %H:%M:%S"
