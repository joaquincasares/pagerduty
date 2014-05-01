#!/usr/bin/env python

import datetime
import calendar
import getpass
import json
import os
import requests
import subprocess
import shlex
import sys
import time

import ConfigParser

api_token = None
authenticated = False

time_format = '%Y-%m-%dT%H:%M:%S'

class TokenAuth(requests.auth.AuthBase):
    """Attaches PagerDuty Token Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = "Token token=%s" % self.token
        return r


def get_authentication():
    global domain
    global api_token
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
        api_token = config.get('PagerDuty', 'api_token') if config.has_option('PagerDuty', 'api_token') else raw_input('PagerDuty API Token: ')
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
        end_date = (now + datetime.timedelta(days=92)).strftime('%Y-%m-%d')

    return requests.get('https://%s.pagerduty.com/api/v1/schedules/%s/entries' %
                        (domain, schedule_id),
                        auth=TokenAuth(api_token),
                        params={'since': start_date, 'until': end_date}).json()


def get_user_schedule(schedule_id=False, needle_name=False, schedule=False):
    if not schedule:
        schedule = get_schedule(schedule_id)

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

def get_open_incidents(just_count=False):
    get_authentication()

    count_parameter = ''
    if just_count:
        count_parameter = '/count'

    return requests.get('https://%s.pagerduty.com/api/v1/incidents%s' %
                        (domain, count_parameter),
                        auth=TokenAuth(api_token),
                        params={'status': 'triggered,acknowledged'}).json()

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
    print '====================='
    print get_open_incidents()
    print '====================='
    print get_open_incidents(just_count=True)
