Description
-----------

Allows for an easy to use interface for grabbing PagerDuty schedules from the
command line. You can grab the PagerDuty schedules for a primary and secondary
schedule in the following fashions:

* Today
* Tomorrow
* This week
* The next 90 days
* The next 90 days for a user

It also allow for emails to be sent out for:

* Who's on call today
* Who's on call this week

Also included is a simple to use widget for ZenDesk that only requires a quick
and simple setup on an external setup. This allows the ZenDesk interface to
incorporate a "Who's on Call" feature for easier reminders.

Setup
-----

First install the requests package by running:

    pip install requests

Move `pagerduty.cfg` to `~/.pagerduty.cfg` to configure and begin.

Run `./cli.py` to get a full list of options.

ZenDesk Widget
--------------

Setup `zendesk-widget.py` on a server along with `~/.pagerduty.cfg` and `pagerduty.py`
then go to {ZenDesk} -> Settings -> Extensions and add a widget with this as the content:

    <iframe src="<url>/zendesk-widget.py"></iframe>

Navigate to the ZenDesk pages that you wish for the widget to appear on and click
"Edit widgets on this page" to add the widget.
