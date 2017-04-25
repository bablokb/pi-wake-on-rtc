Introduction
============

This project implements a *wake-on-rtc* solution for the Raspberry Pi and
other small computers based on the DS3231 real-time-clock.


Overview
--------

The solution consists of two parts: a circuit doing the actual power switching
and secondly some programs to control the rtc.

The circuit reacts to three events

  - a push of the power-on button: this will switch power on and boot the pi
  - an alarm of the rtc: this will also turn power on
  - a gpio-interrupt from the pi after shutdown: this will switch off power

The software-part takes care to program the alarm of the rtc before shutdown,
so the system will boot at the requested time.


Hardware
--------

On the hardware side, you will need a Pi (or compatible computer), a DS3231
and various components for the circuit. See
[doc/circuit.md](./doc/circuit.md "The switching circuit") for details. The
total cost of all parts (execpt Pi) should be around 25€.

Note that the DS3231 is not a perfect solution for wake-on-rtc, since the
alarms in the clock will fire on every match of day-of-month, hour, minute
and seconds. So it is not possible to set the alarm to say May 6, but only
to day six of the next month.

This limitation should be no problem on normal operation, but it is
important to keep in mind that the time-horizon of the clock is only
about a month.


Software
--------

The software consists of a program to control the rtc and a system daemon
which takes care of clearing alarms after boot and setting the alarm (next
boot time) at shutdown. For installation, see the next section.


Installation
============

Clone the archive and then run the install-command from the tools-directory:

    git clone https://github.com/bablokb/pi-wake-on-rtc.git
    cd pi-wake-on-rtc
    sudo tools/install

Besides changing some system configuration files, this command will
mainly install three components:

  - `rtcctl`, the control program for the real-time-clock
  - `wake-on-rtc.service`, the systemd-service
  - an udev-rule to update the system-time from the rtc at boot


Configuration
=============

System configuration
--------------------

The install-command will automatically configure the system. Nevertheless,
please check the modified files `/boot/config.txt` and `/etc/modules`,
especially if you don't start from a vanilla Raspbian.

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

Note that the standard linux tool `hwclock` will not work, since we don't
expose the standard rtc-device interface of the rtc.

The install-command will add an udev-rule which updates the system time
at every boot from the rtc. Also, at shutdown the current system time
is written back to the rtc, but this is configurable.


Service configuration
---------------------

The systemd-service `wake-on-rtc.service` is the central software component
to manage the rtc. At boot time it will clear any existing alarms. At
shutdown, it will set the alarm of the rtc to the next boot time.

The configuration of the service is in `/etc/wake-on-rtc.conf`. For a detailed
explanation of all options, you should read the comments in the file.
The most important options are in the sections `[boot]` and ¸[halt]`:

    [boot]
    hook_cmd: my_special_boot_script
    auto_halt: 0

    [halt]
    next_boot: next_boot.sh
    lead_time: 2
    set_hwclock: 1

If you provide `hook_cmd`, the script will be called either with the parameter
"normal" or "alarm", the latter only in the case the system was powered
on due to a rtc-alarm. Use this script if you need to take special measures
depending on the power-on mode.

With `next_boot` in the section `[halt]` you provide a program or script
which returns the next boot time of the system as a single line of output.
Valid formats are

  - YYYY-mm-dd HH:MM:SS
  - mm/dd/YYYY HH:MM:SS
  - dd.mm.YYYY HH:MM:SS

You can leave away the seconds part and also use only two-digit years.
If the next boot time is unknown, the program should just return a zero.

`lead_time` is interpreted in minutes and will be substracted from
the boot-time returned by the `next_boot` script.

`auto_halt` is a feature to work around the limitation of the DS3231.
If the wake-on-rtc service detects at boot time that the requested
boot-time is actually not reached, it will shutdown automatically again.

To enable the feature, you have to set the value of `auto_halt` to a
positve integer interpreted as minutes. If the next boot time is more than
the given number of minutes in the future, the system shuts down again
automatically. Setting the value of `auto_halt` to less than about 15
does not make much sense.


Usage
=====

The command `/usr/local/sbin/rtcctl` is the main user-interface to the
real time clock. With this command, you can read and write the RTC-time,
set the alarm times, turn the alarms on, off or clear an alarm that has
fired:

    [root@pi2:~] # rtcctl help

    Available commands (date and time are synonyms):
         help                                - dump list of available commands
         show  [date|time|alarm1|alarm2|sys]
                                             - display given type or all
         dump  [control|status|alarm1|alarm2]
                                             - display registers (hex/binary format)
         set   date|time|alarm1|alarm2|sys   - set date/time, alarm1, alarm2 times
                                               Format: dd.mm.YYYY [HH:MM[:SS]] or
                                                       mm/dd.YYYY [HH:MM[:SS]]
                                               (does not turn alarm on!)
         on    alarm1|alarm2                 - turn alarm1/alarm2 on
         off   alarm1|alarm2                 - turn alarm1/alarm2 off
         clear alarm1|alarm2                 - clear alarm1/alarm2-flag

