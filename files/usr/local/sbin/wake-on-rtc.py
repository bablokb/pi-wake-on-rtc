#!/usr/bin/python
# --------------------------------------------------------------------------
# Script executed by systemd service for wake-on-rtc.service.
#
# Please edit /etc/wake-on-rtc.conf to configure the script.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-wake-on-rtc
#
# --------------------------------------------------------------------------

import os, subprocess, sys, syslog, signal
import datetime, re
import ConfigParser

import ds3231

# --- helper functions   ---------------------------------------------------

# --------------------------------------------------------------------------

def write_log(msg):
  global debug, fp_log
  if debug == '1':
    syslog.syslog(msg)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fp_log.write("[" + now + "] " + msg+"\n")
    fp_log.flush()

# --------------------------------------------------------------------------

def get_config(cparser):
  """ parse configuration """
  global debug
  cfg = {}

  debug = cparser.get('GLOBAL','debug')
  alarm = cparser.getint('GLOBAL','alarm')
  i2c   = cparser.getint('GLOBAL','i2c')
  utc   = cparser.getint('GLOBAL','utc')
  
  if cparser.has_option('boot','hook_cmd'):
    boot_hook = cparser.get('boot','hook_cmd')
  else:
    boot_hook = None
  if cparser.has_option('boot','auto_halt'):
    auto_halt = cparser.getint('boot','auto_halt')
  else:
    auto_halt = 0

  next_boot   = cparser.get('halt','next_boot')
  lead_time   = cparser.getint('halt','lead_time')
  set_hwclock = cparser.get('halt','set_hwclock')

  return {'alarm':       alarm,
          'i2c':         i2c,
          'utc':         utc,
          'boot_hook':   boot_hook,
          'auto_halt':   auto_halt,
          'next_boot':   next_boot,
          'lead_time':   lead_time,
          'set_hwclock': set_hwclock}

# --- convert time-string to datetime-object   -----------------------------

def get_datetime(dtstring):
  if '/' in dtstring:
    format = "%m/%d/%Y %H:%M:%S"
  elif '-' in dtstring:
    format = "%Y-%m-%d %H:%M:%S"
  else:
    format = "%d.%m.%Y %H:%M:%S"

  # add default hour:minutes:secs if not provided
  if ':'  not in dtstring:
    dtstring = dtstring + " 00:00:00"

  # parse string and check if we have six items
  dateParts= re.split('\.|/|:|-| ',dtstring)
  count = len(dateParts)
  if count < 5 or count > 6:
    raise ValueError()
  elif count == 5:
    dtstring = dtstring + ":00"

  if '-' in dtstring and len(dateParts[0]) == 2 or (
    '-' not in dtstring and len(dateParts[2]) == 2):
    format = format.replace('Y','y')

  return datetime.datetime.strptime(dtstring,format)

# --- query next boot-time   -----------------------------------------------

def get_boottime():
  global config
  write_log("executing next_boot-hook %s" % config['next_boot'])
  proc = subprocess.Popen(config['next_boot'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  (boot_time,err) = proc.communicate(None)
  write_log("raw boot time: %s" % boot_time)
  if len(err) > 0:
    write_log("error text of next_boot-hook: %s" % err)
    raise ValueError(err)
  elif len(boot_time) < 8:
    return None
  boot_dt = get_datetime(boot_time.strip())
  write_log("raw boot_dt: %s" % boot_dt)

  # substract lead_time
  lead_delta = datetime.timedelta(minutes=config['lead_time'])
  boot_dt = boot_dt - lead_delta
  write_log("calculated boot_dt: %s" % boot_dt)

  return boot_dt

# --- system startup   -----------------------------------------------------

def process_start():
  """ system startup """
  global config
  write_log("processing system startup")
  alarm = config['alarm']

  # check alarm
  rtc = ds3231.ds3231(config['i2c'],config['utc'])
  (enabled,fired) = rtc.get_alarm_state(alarm)
  mode = "alarm" if enabled and fired else "normal"
  write_log("startup-mode: %s" % mode)

  # clear and disable alarm
  rtc.clear_alarm(alarm)
  rtc.set_alarm(alarm,0)
  write_log("alarm %d cleared and disabled" % alarm)

  # create status-file /var/run/wake-on-rtc.status
  with  open("/var/run/wake-on-rtc.status","w") as sfile:
    sfile.write(mode)

  # execute hook-command
  if config['boot_hook']:
    write_log("executing boot-hook %s" % config['boot_hook'])
    try:
      os.system("%s %s &" % (config['boot_hook'],mode))
    except:
      syslog.syslog("Error while executing boot-hook: %s" % sys.exc_info()[0])

  # check if we need to shutdown
  if mode == "alarm" and config['auto_halt'] > 0:
    write_log("processing auto_halt: checking for next boot-time")
    try:
      boot_dt = get_boottime()
      if boot_dt:
        # calculate now+auto_halt
        limit_dt = (datetime.datetime.now() +
                    datetime.timedelta(minutes=config['auto_halt']))
        write_log("now+auto_halt: %s" % limit_dt)
        if boot_dt > limit_dt:
          write_log("next boot-time is after limit. Shutting down!")
          os.system("shutdown -P +1 &")
    except:
      syslog.syslog("Error while auto_halt uprocessing: %s" % sys.exc_info()[0])

# --- system shutdown   ----------------------------------------------------

def process_stop():
  """ system shutdown """
  global config
  write_log("processing system shutdown")
  alarm = config['alarm']

  # set alarm
  rtc = ds3231.ds3231(config['i2c'],config['utc'])
  try:
    boot_dt = get_boottime()
    if boot_dt:
      rtc.set_alarm_time(alarm,boot_dt)
      write_log("alarm %d set to %s" % (alarm,boot_dt))
      rtc.set_alarm(alarm,1)
      write_log("alarm %d enabled" % alarm)
  except:
    syslog.syslog("Error while setting alarm-time: %s" % sys.exc_info()[0])

  # update hwclock from system-time
  if config['set_hwclock'] == 1:
    rtc.write_system_datetime_now()
    write_log("updated rtc-clock from system-time")

# --------------------------------------------------------------------------

def signal_handler(_signo, _stack_frame):
  """ signal-handler for cleanup """
  write_log("interrupt %d detected, exiting" % _signo)
  sys.exit(0)

# --- main program   -------------------------------------------------------

syslog.openlog("wake-on-rtc")
fp_log = open("/var/log/wake-on-rtc.log","at")

parser = ConfigParser.RawConfigParser(
  {'debug': '0',
   'alarm': 1,
   'i2c': 1,
   'utc': 1})
parser.read('/etc/wake-on-rtc.conf')
config = get_config(parser)
write_log("Config: " + str(config))

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
  if len(sys.argv) != 2:
    write_log("missing argument")
  elif sys.argv[1] == "start":
    process_start()
  elif sys.argv[1] == "stop":
    process_stop()
  else:
    write_log("unsupported argument")
except:
  syslog.syslog("Error while executing service: %s" % sys.exc_info()[0])
  raise
fp_log.close()
