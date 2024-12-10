import argparse
import json

import re
import random
import smtplib, ssl
import datetime
from time import sleep
# import pytz
import time
import socket
import sys
import getopt
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

help_message = '''
To use, fill out config.yml with your own participants. You can also specify
DONT-PAIR so that people don't get assigned their significant other.

You'll also need to specify your mail server settings. An example is provided
for routing mail through gmail.

For more information, see README.
'''

REQUIRED_FIELDS = (
    'PARTICIPANTS',
    'SUBJECT',
    'BUDGET'
)


def choose_random_person(candidates):
    return random.choice(candidates)


def create_random_pairs(givers, receivers, pairs=[]):
    if len(givers) == 0:
        return True
    giver = choose_random_person(givers)
    givers.remove(giver)
    rejected_receivers = []
    while True:
        receiver = choose_random_person(receivers)
        if receiver not in rejected_receivers:
            if is_valid_pair(giver, receiver):
                receivers.remove(receiver)
                successful_path = create_random_pairs(givers, receivers, pairs)
                if successful_path:
                    pairs.append((giver, receiver))
                    return True
                else:
                    receivers.append(receiver)
            else:
                rejected_receivers.append(receiver)
        elif len(rejected_receivers) == len(receivers):
            givers.append(giver)
            return False


def is_valid_pair(person1, person2):
    if person1.get("name") == person2.get("name"):
        return False
    if person2.get("name") in person1.get("dont-pair"):
        return False
    if person1.get("name") in person2.get("dont-pair"):
        return False
    return True


def notify_person(email_to, subject, message, config):
    smtp_conf = config.get("SMTP_CONFIG")
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_conf.get("sender")
    msg['To'] = email_to
    msg.attach(MIMEText(message, 'html'))
    # Create a secure SSL context
    context = ssl.create_default_context()
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_conf.get("host"), smtp_conf.get("port"))
        server.starttls() # Secure the connection
        server.login(smtp_conf.get("sender"), smtp_conf.get("password"))
        server.sendmail(smtp_conf.get("sender"), email_to, msg.as_string())
        print("An email was sent to " + email_to)
    except Exception as e:
        print(e)
    finally:
        server.quit()


def get_message(template_message, santa, santee, budget):
    return template_message.replace("{santa}", santa).replace("{santee}", santee).replace("{budget}", budget)


def main(args):
    try:
        # ------------------------------------------------------------------------------------------------------------
        # Read config file
        if args.config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        else:
            config_file = args.config_file
        if not os.path.exists(config_file):
            raise Exception(f"Invalid config file {config_file}.")

        config = json.loads(open(config_file, 'r').read())
        for key in REQUIRED_FIELDS:
            if key not in config.keys():
                raise Exception(f'Required parameter {key} not in config file. Unable to continue.')

        # Read email template file
        if args.email_template is None:
            email_template = os.path.join(os.path.dirname(__file__), 'email_template.html')
        else:
            email_template = args.email_template

        if not os.path.exists(email_template):
            raise Exception(f"Invalid email template file {email_template}.")

        with open(email_template, 'r') as template_file:
            MESSAGE_TEMPLATE = template_file.read()

        # ------------------------------------------------------------------------------------------------------------
        # Check participants information
        participants = config.get('PARTICIPANTS')
        if len(participants) < 2:
            raise Exception('Not enough participants specified. Unable to continue.')
        emails = {}
        names = {}
        for person in participants:
            if person.get("email") is None or person.get("name") is None:
                raise Exception(f"Invalid information for person (empty name or email).")
            if person.get("email") in emails and not args.ignore_repeated_emails:
                raise Exception(f"Duplicated email {person.get('email')}")
            else:
                emails[person.get("email")] = person
            if person.get("name") in names:
                raise Exception(f"Duplicated person name {person.get('name')}")
            else:
                names[person.get("name")] = person
            # Convert dont pair to a set
            person["dont-pair"] = set(person.get("dont-pair", []))
        # Validate and fill the "dont-pair" field for all the participants
        for person in participants:
            for person_name in person.get("dont-pair", []):
                if person_name not in names:
                    raise Exception(f"Invalid person  {person_name} in 'dont-pair' for {person.get('name')}")
                else:
                    # If the person name is valid, then add the same rule to the other person
                    dont_pair = names.get(person_name).get("dont-pair", set())
                    dont_pair.add(person.get("name"))
                    names.get(person_name)["dont-pair"] = dont_pair
        # ------------------------------------------------------------------------------------------------------------
        # Create the random pairs
        pairs = []
        create_random_pairs(participants, [] + participants, pairs)
        # Now send the emails or show the summary if testing
        print("Pairs are:")
        for pair in pairs:
            print(f"{pair[0].get('name')} give a present to {pair[1].get('name')}")
        print("To send out real emails with new pairings, run with the --send argument:")
        print("$ python secret_santa.py --send")
        for pair in pairs:
            subject = config.get("SUBJECT")
            message = get_message(MESSAGE_TEMPLATE, pair[0].get("name"), pair[1].get("name"), str(config['BUDGET']))
            if not args.send:
                email = config.get("SMTP_CONFIG").get("sender", "email@gmail.com")
            else:
                email = pair[0].get("email")
            notify_person(email, subject, message, config)
            sleep(2)
    except Exception as ex:
        print(str(ex))


def parse_args(args):
    """
    This function reads and process the params for the script.
    :param args: the arguments for the script
    :return: the processed arguments
    """
    parser = argparse.ArgumentParser(description="Arguments for database_process.py")
    parser.add_argument("--send", help="Send real emails, by default emails are sent to me", action="store_true", required=False)
    parser.add_argument("--config-file", help="The config file to use. If not provided, local config.json will be used.", required=False)
    parser.add_argument("--email-template", help="The template file for the email to be sent", required=False)
    parser.add_argument("--ignore-repeated-emails", help="Ignore repeated emails", action="store_true", required=False)
    return parser.parse_args(args)


if __name__ == "__main__":
    main(parse_args(sys.argv[1:]))
