Intro
=====

Secret-Santa helps you manage a list of participants for gift exchanges by randomly assigning pairings and sending emails. It can prevent pairing couples with their significant other and allows you to customize the email messages.

Dependencies
------------

pytz
pyyaml

Usage
-----

Copy config-example.json to config.yml and change the connection details
for your SMTP server.
Modify the participants and the email message if you wish.

Once configured, call secret-santa this won't send the emails to the "real receivers":

`python secret_santa.py`

To send out the real emails with new pairings, call with the --send argument:

`$ python secret_santa.py --send`
