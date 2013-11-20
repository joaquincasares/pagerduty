#!/usr/bin/env python

import os
import shelve
import sys
import time

import ConfigParser

import cli
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

def generate_page():
    try:
        d = shelve.open('pagerduty.db')
        if not d.has_key('full_listing') or (time.time() - d['full_listing']['last_pulled']) > cache_timeout:
            # Pull full_schedule
            global secondary
            primary = pagerduty.get_user_schedule()
            if secondary:
                secondary = pagerduty.get_user_schedule(secondary)

            # Save pulled information
            packaged_dict = {}
            packaged_dict['last_pulled'] = time.time()
            packaged_dict['result'] = cli.format_results(primary, secondary, True)
            d['full_listing'] = packaged_dict
    finally:
        result = d['full_listing']['result']
        d.close()

    return """Content-Type: text/html\n
    <link href="pagerduty.css" media="all" rel="stylesheet" type="text/css" />
    <body class='full_schedule'>\n%s
    </body>
    """ % result

def main():
    read_configurations()
    print generate_page()

if __name__ == "__main__":
    main()
