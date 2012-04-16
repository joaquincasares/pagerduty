#!/usr/bin/env python

import os
import smtplib
import sys

import ConfigParser

from optparse import OptionParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from optparse import OptionParser

import pagerduty


options = False
config = False
secondary = False

def email_msg(subject, msg_to, text, html):
    msg_from = '"Pager Duty Scheduling"'

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = ''
    if reply_to:
        msg.add_header('reply-to', reply_to)

    # Setup bcc email addresses
    bcc = ['']
    msg_to = filter(None, msg_to + bcc)

    part1 = MIMEText(text, 'plain')
    msg.attach(part1)

    part2 = MIMEText(html, 'html')
    msg.attach(part2)

    # Send the message via gmail SMTP server.
    s = smtplib.SMTP(config.get('SMTP', 'server'))
    s.starttls()
    s.login(config.get('SMTP', 'email'),config.get('SMTP', 'password'))
    s.sendmail(msg_from, msg_to, msg.as_string())
    s.quit()



def format_results(primary, secondary=False, html=False):
    if not secondary:
        dates = primary.keys()
        dates.sort()

        placeholder = '{0:40}{1:30}\n'
        if html:
            placeholder = '<tr><td>{0}</td><td>{1}</td></tr>\n'

        result = placeholder.format('Shift Start', 'Primary')
        for date in dates:
            result += placeholder.format(primary[date]['shift_start'], primary[date]['agent_name'])
    else:
        dates = primary.keys() + secondary.keys()
        dates = set(dates)
        dates = sorted(dates)

        placeholder = '{0:40}{1:30}{2:30}\n'
        if html:
            placeholder = '<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>\n'

        result = placeholder.format('Shift Start', 'Primary', 'Secondary')
        for date in dates:
            shift_start = primary[date]['shift_start'] if date in primary else secondary[date]['shift_start']
            primary_agent = primary[date]['agent_name'] if date in primary else ''
            secondary_agent = secondary[date]['agent_name'] if date in secondary else ''

            result += placeholder.format(shift_start, primary_agent, secondary_agent)

    if html:
        return '<table border="1" cellpadding="5">\n%s</table>' % result
    return result

def extract_emails(primary, secondary=False):
    email_list = []
    for key in primary.keys():
        email_list.append(primary[key]['agent_email'])
    if secondary:
        for key in secondary.keys():
            email_list.append(secondary[key]['agent_email'])
    email_list = set(email_list)
    email_list = sorted(email_list)
    return email_list

def list_user_90_days(user):
    global secondary
    primary = pagerduty.get_user_schedule(needle_name=user)
    if secondary:
        secondary = pagerduty.get_user_schedule(secondary, needle_name=user)
    print format_results(primary, secondary)

def list_90_days():
    global secondary
    primary = pagerduty.get_user_schedule()
    if secondary:
        secondary = pagerduty.get_user_schedule(secondary)
    print format_results(primary, secondary)

def list_day():
    global secondary
    primary = pagerduty.get_daily_schedule()
    if secondary:
        secondary = pagerduty.get_daily_schedule(secondary)
    print format_results(primary, secondary)

def list_tomorrow():
    global secondary
    primary = pagerduty.get_tomorrows_schedule()
    if secondary:
        secondary = pagerduty.get_tomorrows_schedule(secondary)
    print format_results(primary, secondary)

def list_week():
    global secondary
    primary = pagerduty.get_weekly_schedule()
    if secondary:
        secondary = pagerduty.get_weekly_schedule(secondary)
    print format_results(primary, secondary)

def email_today():
    global secondary
    primary = pagerduty.get_daily_schedule()
    if secondary:
        secondary = pagerduty.get_daily_schedule(secondary)

    email = """Hello,

We wanted to notify you that you're on call today.

Once again, the Support Team appreciates your contributions. However, if you cannot fulfill your duty, please notify your backup immediately. It is vital for you to communicate this with your teammate.

%s
Thanks,
The Support Team
    """

    txt = email % format_results(primary, secondary)
    html = email.replace('\n', '<br>\n') % format_results(primary, secondary, html=True)

    print txt
    email_list = extract_emails(primary, secondary)
    print 'Email list: %s' % email_list

    if bypass_prompts or raw_input('Send email? [y/N] ').lower() == 'y':
        email_msg("You're on call today", email_list, txt, html)
        print "Daily Support Schedule Emailed!"
    else:
        print "Email not sent."

def email_week():
    global secondary
    primary = pagerduty.get_weekly_schedule()
    if secondary:
        secondary = pagerduty.get_weekly_schedule(secondary)

    email = """Hello Team,

Below is the Pager Duty schedule for this week.

Once again, the Support Team appreciates your contributions. However, if you cannot fulfill your duty, please notify your backup immediately. It is vital for you to communicate this with your teammate.

%s
Thanks,
The Support Team
    """

    txt = email % format_results(primary, secondary)
    html = email.replace('\n', '<br>\n') % format_results(primary, secondary, html=True)

    print txt
    email_list = extract_emails(primary, secondary)
    print 'Email list: %s' % email_list

    if bypass_prompts or raw_input('Send email? [y/N] ').lower() == 'y':
        email_msg("You're on call this week", email_list, txt, html)
        print "Weekly Support Schedule Emailed!"
    else:
        print "Email not sent."



def read_configurations():
    global config
    global secondary
    global bypass_prompts
    global reply_to
    configfile = os.path.join(os.path.expanduser('~'), '.pagerduty.cfg')
    if not os.path.exists(configfile):
        sys.stderr.write('Move pagerduty.cfg to ~/.pagerduty.cfg to begin.\n')
        sys.exit(1)
    config = ConfigParser.RawConfigParser()
    config.read(configfile)

    secondary = config.get('Cli', 'secondary_schedule') if config.has_option('Cli', 'secondary_schedule') else False
    bypass_prompts = config.get('Cli', 'bypass_prompts') if config.has_option('Cli', 'bypass_prompts') else False
    bypass_prompts = bypass_prompts.lower() == 'true'
    reply_to = config.get('Cli', 'reply_to') if config.has_option('Cli', 'reply_to') else False

def parse_options():
    global options
    global parser
    parser = OptionParser()
    parser.add_option("-u", "--user", dest="user",
                      help="Show a user's rotations")
    parser.add_option("-d", "--day", dest="day",
                      action="store_true", help="Show today's schedule")
    parser.add_option("-t", "--tomorrow", dest="tomorrow",
                      action="store_true", help="Show tomorrow's schedule")
    parser.add_option("-w", "--week", dest="week",
                      action="store_true", help="Show the week's schedule")
    parser.add_option("-l", "--list", dest="list",
                      action="store_true", help="List the next 90 days")
    parser.add_option("--email_today", dest="email_today",
                      action="store_true", help="Email the today's schedule")
    parser.add_option("--email_week", dest="email_week",
                      action="store_true", help="Email the current week's schedule")

    (options, args) = parser.parse_args()

def main():
    parse_options()
    read_configurations()

    if len(sys.argv) > 1:
        if options.user:
            list_user_90_days(options.user)
        elif options.list:
            list_90_days()
        elif options.day:
            list_day()
        elif options.tomorrow:
            list_tomorrow()
        elif options.week:
            list_week()
        elif options.email_today:
            email_today()
        elif options.email_week:
            email_week()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print
