#!/usr/bin/env python

import ast
import datetime
import calendar
import getpass
import json
import os
import subprocess
import shlex
import sys
import time
import urllib2

import ConfigParser

admin_email = False
admin_password = False
authenticated = False

time_format = '%Y-%m-%dT%H:%M:%S'

def get_authentication():
    global domain
    global admin_email
    global admin_password
    global primary_schedule
    global shift_start_hour
    global authenticated

    if authenticated:
        return

    configfile = os.path.join(os.path.expanduser('~'), '.pagerduty.cfg')

    if not os.path.exists(configfile):
        sys.stderr.write('Move pagerduty.cfg to ~/.pagerduty.cfg to begin.\n')
        sys.exit(1)
    else:
        config = ConfigParser.RawConfigParser()
        config.read(configfile)

        domain = config.get('PagerDuty', 'domain') if config.has_option('PagerDuty', 'domain') else raw_input('PagerDuty Domain: ')
        admin_email = config.get('PagerDuty', 'email') if config.has_option('PagerDuty', 'email') else raw_input('PagerDuty Email Address: ')
        admin_password = config.get('PagerDuty', 'pass') if config.has_option('PagerDuty', 'pass') else getpass.getpass()
        primary_schedule = config.get('PagerDuty', 'primary_schedule') if config.has_option('PagerDuty', 'primary_schedule') else raw_input('PagerDuty Schedule ID: ')
        shift_start_hour = int(config.get('PagerDuty', 'shift_start_hour')) * -1 if config.has_option('PagerDuty', 'shift_start_hour') else int(raw_input('Schedule Start Hour: ')) * -1

    authenticated = 'In Progress'
    if "<error>" in get_schedule(primary_schedule):
        sys.stdout.write('Authentication with "%s" failed. Please try again...' % (admin_email))
        sys.exit(1)

    # print 'Successfully authenticated to PagerDuty!'
    authenticated = True


def get_schedule(schedule_id=False, time_period=False, offset_days=False):
    get_authentication()

    if not schedule_id:
        schedule_id = primary_schedule

    offset = datetime.timedelta(days=0)
    if offset_days:
        offset = datetime.timedelta(days=offset_days)
    now = datetime.datetime.today() + offset + datetime.timedelta(hours=shift_start_hour)

    start_date = now.strftime('%Y-%m-%d')
    if time_period == 'day':
        end_date = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    elif time_period == 'week':
        end_date = (now + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        end_date = (now + datetime.timedelta(days=93)).strftime('%Y-%m-%d')

    def basic_authorization(user, password):
        s = user + ":" + password
        return "Basic " + s.encode("base64").rstrip()

    req = urllib2.Request("http://%s.pagerduty.com/api/v1/schedules/%s/entries?since=%s&until=%s" %
                              (domain, schedule_id, start_date, end_date),
                              headers = {"Authorization": basic_authorization(admin_email, admin_password)})
    f = urllib2.urlopen(req)
    return f.read()

def get_user_schedule(schedule_id=False, needle_name=False, schedule=False):
    if not schedule:
        schedule = get_schedule(schedule_id)

    schedule = ast.literal_eval(schedule)

    result = {}
    for entry in schedule['entries'][1:]:
        agent_name = entry['user']['name']
        agent_email = entry['user']['email']
        shift_start = entry['start']

        if not needle_name or needle_name.lower() in agent_name.lower():
            start_time, zone = shift_start[:-6], shift_start[-6:]
            start_stamp = calendar.timegm(time.strptime(start_time, time_format))
            offset_hr, offset_min = int(zone[0:3]), int(zone[0] + zone[-2:])
            real_start_time = start_stamp - (offset_hr * 3600 + offset_min * 60)
            start_date = time.localtime(real_start_time)
            shift_start = time.strftime('%m.%d.%Y - %A (%I%p %Z)', start_date)
            result[start_date] = {
                'agent_name': agent_name,
                'agent_email': agent_email,
                'shift_start': shift_start
            }
    return result

def get_daily_schedule(schedule_id=False):
    schedule = get_schedule(schedule_id, time_period='day')
    return get_user_schedule(schedule_id, schedule=schedule)

def get_tomorrows_schedule(schedule_id=False):
    schedule = get_schedule(schedule_id, time_period='day', offset_days=1)
    return get_user_schedule(schedule_id, schedule=schedule)

def get_weekly_schedule(schedule_id=False):
    schedule = get_schedule(schedule_id, time_period='week')
    return get_user_schedule(schedule_id, schedule=schedule)



if __name__ == "__main__":
    print 'Running basic tests:'
    print get_user_schedule()
    print '====================='
    print get_user_schedule(needle_name='joaquin')
    print '====================='
    print get_daily_schedule()
    print '====================='
    print get_tomorrows_schedule()
    print '====================='
    print get_weekly_schedule()
