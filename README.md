Introduction
============

This project implements a *wake-on-rtc* solution for the Raspberry Pi and
other small computers.

Overview
--------

Hardware
--------

Software
--------


Installation
============

Clone the archive and run then run the install-command from the tools-directory:

    git clone https://github.com/bablokb/pi-wake-on-rtc.git
    cd pi-wake-on-rtc
    sudo tools/install


Configuration
=============

System configuration
--------------------

The install-command will automatically configure the system. Nevertheless,
please check the modified files `/boot/config.txt` and `/etc/modules`.
Make sure you don't load the standard DS3231-driver from `/boot/config.txt`:
you should remove or comment out the following line:

    dtoverlay=i2c-rtc,ds3231


Initializing the real-time-clock
--------------------------------

If your real-time-clock is not yet set, you have to initilize it once.
Make sure that you have an internet connection so the ntp-daemon updates
the system time. Check the system time and the time of the rtc:

    date
    sudo rtcctl show date

If the system time is correct and the time matches, you are done. Otherwise
write the system time to the rtc:

    sudo rtcctl set date


Service configuration
---------------------


Usage
=====

The command `/usr/local/sbin/rtcctl` is the main user-interface to the
real time clock. With this command, you can read and write the RTC-time,
set the alarm times, turn the alarms on, off or clear an alarm that has
fired:

    [root@pi2:~] # rtcctl help

    Available commands (date and time are synonyms):
         help                                - dump list of available commands
         show  [date|time|alarm1|alarm2|
                                   sys|all]  - display given type or all
         dump  [control|status|alarm1|
                               alarm2|all]   - display registers (hex/binary format)
         set   date|time|alarm1|alarm2|sys   - set date/time, alarm1, alarm2 times
                                               Format: dd.mm.YYYY [HH:MM[:SS]] or
                                                       mm/dd.YYYY [HH:MM[:SS]]
                                               (does not turn alarm on!)
         on    alarm1|alarm2                 - turn alarm1/alarm2 on
         off   alarm1|alarm2                 - turn alarm1/alarm2 on
         clear alarm1|alarm2                 - clear alarm1/alarm2-flag

