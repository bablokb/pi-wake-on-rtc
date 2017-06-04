#!/bin/bash
# --------------------------------------------------------------------------
# Sample command to query next boot time.
#
# This script would typically query a sort of database, but it could also
# hardwire the next boot time (see examples below).
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-wake-on-rtc
#
# --------------------------------------------------------------------------

# no wakeup
echo "0"

# next wakeup in 5 minutes
#date -d "now + 5 minutes" +"%Y-%m-%d %H:%M:%S"

# next wakeup tomorrow at 08:00
#date -d "tomorrow 08:00" +"%Y-%m-%d %H:%M:%S"

