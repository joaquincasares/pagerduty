Setup
=====

Move `pagerduty.cfg` to `~/.pagerduty.cfg` to configure and begin.

Run `./cli.py` to get a full list of options.

ZenDesk Widget
==============

Setup `zendesk-widget.py` on a server along with `~/.pagerduty.cfg` and `pagerduty.py`
then go to {ZenDesk} -> Settings -> Extensions and add a widget with this as the content:

    <iframe src="<url>/zendesk-widget.py"></iframe>

Navigate to the ZenDesk pages that you wish for the widget to appear on and click
"Edit widgets on this page" to add the widget.
