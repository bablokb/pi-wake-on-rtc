#!/usr/bin/env python
"""
# --------------------------------------------------------------------------
# Low-level python interface for the RTC DS3231.
#
# Original code from: https://github.com/switchdoclabs/RTC_SDL_DS3231
# forked from:        https://github.com/conradstorz/RTC_SDL_DS3231
#
# This version adds alarm-handling and various fixes and simplifications
# to the original code.
#
# Author: Bernhard Bablok (methods related to alarms, various changes and fixes)
# License: see below (license statement of the original code)
#
# Website: https://github.com/bablokb/pi-wake-on-rtc
#
# --------------------------------------------------------------------------

#encoding: utf-8

# ---------------------- Original header ------------------------------------

# SDL_DS3231.py Python Driver Code
# SwitchDoc Labs 12/19/2014
# V 1.2
# only works in 24 hour mode
# now includes reading and writing the AT24C32 included on the SwitchDoc Labs
#   DS3231 / AT24C32 Module (www.switchdoc.com

# Copyright (C) 2013 @XiErCh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ---------------------- Original header ------------------------------------
"""

import time
import smbus
from datetime import datetime, timedelta
import arrow                                  # local/utc conversions

# set I2c bus addresses of clock module and non-volatile ram 
DS3231ADDR = 0x68 #known versions of DS3231 use 0x68
AT24C32ADDR = 0x57  #older boards use 0x56

I2C_PORT = 1 #valid ports are 0 and 1

def _bcd_to_int(bcd):
    """
    Decode a 2x4bit BCD to a integer.
    """
    out = 0
    for digit in (bcd >> 4, bcd):
        for value in (1, 2, 4, 8):
            if digit & 1:
                out += value
            digit >>= 1
        out *= 10
    return out / 10


def _int_to_bcd(number):
    """
    Encode a one or two digits number to the BCD format.
    """
    bcd = 0
    for idx in (number // 10, number % 10):
        for value in (8, 4, 2, 1):
            if idx >= value:
                bcd += 1
                idx -= value
            bcd <<= 1
    return bcd >> 1


def _set_bit(value,index,state):
    """
    Set bit given by index (zero-based) in value to state and return the result
    """
    mask = 1 << index
    value &= ~mask
    if state:
        value |= mask
    return value

def _local2utc(dtime):
  """
  Convert a naive datetime-object in local-time to UTC
  """
  a = arrow.get(dtime,'local')
  return a.to('utc').naive

def _utc2local(dtime):
  """
  Convert a naive datetime-object in UTC to local-time
  """
  a = arrow.get(dtime,'utc')
  return a.to('local').naive
  
class ds3231(object):
    """
    Define the methods needed to read and update the real-time-clock module.
    """

    _SECONDS_REGISTER      = 0x00
    _MINUTES_REGISTER      = 0x01
    _HOURS_REGISTER        = 0x02
    _DAY_OF_WEEK_REGISTER  = 0x03
    _DAY_OF_MONTH_REGISTER = 0x04
    _MONTH_REGISTER        = 0x05
    _YEAR_REGISTER         = 0x06

    _ALARM1_OFFSET         = 0x07
    _ALARM1_SEC_REGISTER   = 0x07
    _ALARM1_MIN_REGISTER   = 0x08
    _ALARM1_HOUR_REGISTER  = 0x09
    _ALARM1_DATE_REGISTER  = 0x0A

    _ALARM2_OFFSET         = 0x0B
    _ALARM2_MIN_REGISTER   = 0x0B
    _ALARM2_HOUR_REGISTER  = 0x0C
    _ALARM2_DATE_REGISTER  = 0x0D

    _CONTROL_REGISTER      = 0x0E
    _STATUS_REGISTER       = 0x0F

    _AGING_REGISTER        = 0x10             # unused
    _TEMP_MSB_REGISTER     = 0x11
    _TEMP_LSB_REGISTER     = 0x12

    def __init__(self, port=I2C_PORT, utc=True,addr=DS3231ADDR, at24c32_addr=AT24C32ADDR):
        """
        ???
        """
        self._bus = smbus.SMBus(port) #valid ports are 0 and 1
        self._utc = utc
        self._addr = addr
        self._at24c32_addr = at24c32_addr

    ###########################
    # DS3231 real time clock functions
    ###########################
    
    def _write(self, register, data):
        """
        ???
        """
        self._bus.write_byte_data(self._addr, register, data)

    def _read(self, data):
        """
        ???
        """
        return self._bus.read_byte_data(self._addr, data)

    def _read_seconds(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._SECONDS_REGISTER) & 0x7F)   # wipe out the oscillator on bit

    def _read_minutes(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._MINUTES_REGISTER))

    def _read_hours(self):
        """
        ???
        """
        tmp = self._read(self._HOURS_REGISTER)
        if tmp == 0x64:
            tmp = 0x40
        return _bcd_to_int(tmp & 0x3F)

    def _read_day(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._DAY_OF_WEEK_REGISTER))

    def _read_date(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._DAY_OF_MONTH_REGISTER))

    def _read_month(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._MONTH_REGISTER) & 0x1F)

    def _read_year(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._YEAR_REGISTER))

    def read_all(self):
        """
        Return a tuple such as (year, month, daynum, dayname, hours, minutes, seconds).
        """
        return (self._read_year(), self._read_month(), self._read_date(),
                self._read_day(), self._read_hours(), self._read_minutes(),
                self._read_seconds())

    def read_str(self):
        """
        Return a string such as 'YY-DD-MMTHH-MM-SS'.
        """
        return '%02d-%02d-%02dT%02d:%02d:%02d' % (self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds())

    def read_datetime(self):
        """
        Return the datetime.datetime object.
        """
        dtime =  datetime(2000 + self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds(), 0)
        if (self._utc):
          return _utc2local(dtime)
        else:
          return dtime

    def write_all(self, seconds=None, minutes=None, hours=None, day_of_week=None,
            day_of_month=None, month=None, year=None):
        """
        Direct write each user specified value.
        Range: seconds [0,59], minutes [0,59], hours [0,23],
                 day_of_week [0,7], day_of_month [1-31], month [1-12], year [0-99].
        """
        if seconds is not None:
            if seconds < 0 or seconds > 59:
                raise ValueError('Seconds is out of range [0,59].')
            seconds_reg = _int_to_bcd(seconds)
            self._write(self._SECONDS_REGISTER, seconds_reg)

        if minutes is not None:
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes is out of range [0,59].')
            self._write(self._MINUTES_REGISTER, _int_to_bcd(minutes))

        if hours is not None:
            if hours < 0 or hours > 23:
                raise ValueError('Hours is out of range [0,23].')
            self._write(self._HOURS_REGISTER, _int_to_bcd(hours)) # not  | 0x40 according to datasheet

        if year is not None:
            if year < 0 or year > 99:
                raise ValueError('Years is out of range [0, 99].')
            self._write(self._YEAR_REGISTER, _int_to_bcd(year))

        if month is not None:
            if month < 1 or month > 12:
                raise ValueError('Month is out of range [1, 12].')
            self._write(self._MONTH_REGISTER, _int_to_bcd(month))

        if day_of_month is not None:
            if day_of_month < 1 or day_of_month > 31:
                raise ValueError('Day_of_month is out of range [1, 31].')
            self._write(self._DAY_OF_MONTH_REGISTER, _int_to_bcd(day_of_month))

        if day_of_week is not None:
            if day_of_week < 1 or day_of_week > 7:
                raise ValueError('Day_of_week is out of range [1, 7].')
            self._write(self._DAY_OF_WEEK_REGISTER, _int_to_bcd(day_of_week))

    def write_datetime(self, dtime):
        """
        Write from a datetime.datetime object.
        """
        if(self._utc):
            dtime = _local2utc(dtime)

        self.write_all(dtime.second, dtime.minute, dtime.hour,
                dtime.isoweekday(), dtime.day, dtime.month, dtime.year % 100)

    def write_system_datetime_now(self):
        """
        shortcut version of "DS3231.write_datetime(datetime.datetime.now())".
        """
        self.write_datetime(datetime.now())

    #######################################################################
    # SDL_DS3231 alarm handling. Recurring alarms are currently unsupported.
    ########################################################################
    
    def set_alarm_time(self,alarm,dtime):
        """
        Set alarm to given time-point. Note: although this method has a
        full datetime-value as input, only the values of day-of-month,
        hours, minutes and seconds (only alarm1) are used
        """
        if (self._utc):
            dtime = _local2utc(dtime)

        if alarm == 1:
            self._write(self._ALARM1_SEC_REGISTER, _int_to_bcd(dtime.second))
            self._write(self._ALARM1_MIN_REGISTER, _int_to_bcd(dtime.minute))
            self._write(self._ALARM1_HOUR_REGISTER, _int_to_bcd(dtime.hour))
            self._write(self._ALARM1_DATE_REGISTER, _int_to_bcd(dtime.day))
        else:
            self._write(self._ALARM2_MIN_REGISTER, _int_to_bcd(dtime.minute))
            self._write(self._ALARM2_HOUR_REGISTER, _int_to_bcd(dtime.hour))
            self._write(self._ALARM2_DATE_REGISTER, _int_to_bcd(dtime.day))

    def get_alarm_time(self,alarm,convert=True):
        """
        Query the given alarm and construct a valid datetime-object or
        a tuple (day-of-month/day-of-week,hour,min,sec) depending on the
        convert flag.
        """

        # seconds
        is_interval = False
        if alarm == 1:
            buffer = self._read(self._ALARM1_SEC_REGISTER)
            if buffer & 0x80:
                # we fire every second
                if not convert:
                    return (None,None,None,None,None)
                else:
                    return datetime.now()          # not very sensible
            sec = _bcd_to_int(buffer & 0x7F)
            offset = self._ALARM1_OFFSET + 1
        else:
            sec  = 0
            offset = self._ALARM2_OFFSET

        # minutes
        buffer = self._read(offset)
        if buffer & 0x80:
            # alarm when seconds match
            if not convert:
                return (None,None,None,None,sec)
            else:
                return self._next_dt_match(alarm,None,None,None,None,sec)
        min  = _bcd_to_int(buffer & 0x7F)

        # hour
        offset = offset + 1
        buffer = self._read(offset)
        if buffer & 0x80:
            # alarm when minutes match
            if not convert:
                return (None,None,None,min,sec)
            else:
                return self._next_dt_match(alarm,None,None,None,min,sec)
        hour = _bcd_to_int(buffer & 0x7F)

        # day-in-month/day-of-week
        offset = offset + 1
        buffer = self._read(offset)
        if buffer & 0x80:
            # alarm when hour match
            if not convert:
                return (None,None,hour,min,sec)
            else:
                return self._next_dt_match(alarm,None,None,hour,min,sec)
        elif buffer & 0x40:
            # DY/DT (bit 6) is 1
            weekday  = _bcd_to_int(buffer & 0x3F)
            day = None
        else:
            weekday = None
            day  = _bcd_to_int(buffer & 0x3F)

        if not convert:
            return (day,weekday,hour,min,sec)
        else:
            return self._next_dt_match(alarm,day,weekday,hour,min,sec)

    def _next_dt_match(self,alarm,day,weekday,hour,min,sec):
        # calculate year/month of alarm
        if (self._utc):
            now = datetime.utcnow()
        else:
            now = datetime.now()
        # convert weekday to day of month
        if not weekday == None:
            now = now + timedelta((weekday - now.weekday()+7) % 7)
            day = now.day
        year = now.year
        month = now.month

        enabled,fired = self.get_alarm_state(alarm)

        try:
            alarm_dtime = datetime(year,month,day,hour,min,sec)
        except ValueError:
            # day-of-month might not be valid for current month!
            # no year roll-over necessary, since this won't happen
            # for December or January
            if fired:
                month = month - 1         # alarm must have been in the past
            else:
                month = month + 1         # alarm date is in the future
            alarm_dtime = datetime(year,month,day,hour,min,sec)

        if now > alarm_dtime and not fired:
            # alarm did not fire yet, must be in the future
            month = month + 1
            if month > 12:
                month = 1
                year  = year + 1
        elif now < alarm_dtime and fired:
            # alarm fired, must be in the past
            month = month - 1
            if month == 0:
                month = 12
                year = year - 1

        dtime = datetime(year,month,day,hour,min,sec) 
        if (self._utc):
          return _utc2local(dtime)
        else:
          return dtime

    def get_alarm_state(self,alarm):
        """
        Query if the state of the alarm. Returns a tuple (enabled,fired)
        of two booleans.
        """
        control = self._read(self._CONTROL_REGISTER)
        status  = self._read(self._STATUS_REGISTER)

        return (bool(control & alarm),bool(status & alarm))
    
    def clear_alarm(self,alarm):
        """
        Clear the given alarm (set A1F or A2F in the status-register to zero)
        """
        status = self._read(self._STATUS_REGISTER)
        status &= ~alarm
        self._write(self._STATUS_REGISTER,status)
        
    def set_alarm(self,alarm,state):
        """
        Set the given alarm-flag A1IE or A2IE in the control-register to the
        desired state (0 or 1)
        """
        control = self._read(self._CONTROL_REGISTER)
        control = _set_bit(control,alarm-1,state)
        self._write(self._CONTROL_REGISTER,control)

    def dump_value(self,value):
        """
        Dump a value as hex and binary string
        """
        return "0x{0:02X} 0b{0:08b}".format(value,value)
    
    def dump_register(self,reg):
        """
        Read and return a raw register as binary string
        """
        return self.dump_value(self._read(reg))
    
    ###########################
    # SDL_DS3231 module onboard temperature sensor
    ###########################

    def get_temp(self):
        """
        ???
        """
        byte_tmsb = self._bus.read_byte_data(self._addr, self._TEMP_MSB_REGISTER)
        byte_tlsb = bin(self._bus.read_byte_data(self._addr,
                                            self._TEMP_LSB_REGISTER))[2:].zfill(8)
        return byte_tmsb + int(byte_tlsb[0]) * 2 ** (-1) + int(byte_tlsb[1]) * 2 ** (-2)

    ###########################
    # AT24C32 non-volatile ram Code
    ###########################

    def set_current_at24c32_address(self, address):
        """
        ???
        """
        addr1 = address / 256
        addr0 = address % 256
        self._bus.write_i2c_block_data(self._at24c32_addr, addr1, [addr0])

    def read_at24c32_byte(self, address):
        """
        ???
        """
        self.set_current_at24c32_address(address)
        return self._bus.read_byte(self._at24c32_addr)

    def write_at24c32_byte(self, address, value):
        """
        ???
        """
        addr1 = address / 256
        addr0 = address % 256
        self._bus.write_i2c_block_data(self._at24c32_addr, addr1, [addr0, value])
        time.sleep(0.20)
