#!/usr/bin/env python

import os
import shelve
import sys
import time

import ConfigParser

import pagerduty

cache_timeout = 60 * 60

def read_configurations():
    global config
    global secondary
    configfile = os.path.join(os.path.expanduser('~'), '.pagerduty.cfg')
    if not os.path.exists(configfile):
        sys.stderr.write('Move pagerduty.cfg to ~/.pagerduty.cfg to begin.\n')
        sys.exit(1)
    config = ConfigParser.RawConfigParser()
    config.read(configfile)

    secondary = config.get('Cli', 'secondary_schedule') if config.has_option('Cli', 'secondary_schedule') else False

def format_results(primary, secondary=False):
    if not secondary:
        dates = primary.keys()
        dates.sort()

        result = ''
        for date in dates:
            result += '<h4>Primary</h4>%s<br/>\n' % primary[date]['agent_name'] if date in primary else ''
    else:
        dates = primary.keys() + secondary.keys()
        dates = set(dates)
        dates = sorted(dates)

        result = ''
        for date in dates:
            result += '<h4>Primary</h4>%s<br/>\n' % primary[date]['agent_name'] if date in primary else ''
            result += '<br/>\n'
            result += '<h4>Secondary</h4>%s<br/>\n' % secondary[date]['agent_name'] if date in secondary else ''

    return result

def generate_page():
    global secondary

    primary = pagerduty.get_daily_schedule()
    if secondary:
        secondary = pagerduty.get_daily_schedule(secondary)

    return """Content-Type: text/html\n
    <link href="pagerduty.css" media="all" rel="stylesheet" type="text/css" />\n%s
    <br/>
    <a href="full-schedule.py" target="_blank">Full Schedule</a>
    """ % format_results(primary, secondary)

def save_and_print(d):
    result = generate_page()
    d['on_call'] = {
        'result': result,
        'last_pulled': time.time()
    }
    print result


def main():
    read_configurations()
    try:
        d = shelve.open('pagerduty.db')
        if d.has_key('on_call') and (time.time() - d['on_call']['last_pulled']) < cache_timeout:
            print d['on_call']['result']
        else:
            save_and_print(d)
    finally:
        d.close()

if __name__ == "__main__":
    main()
