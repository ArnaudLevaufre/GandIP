"""

Copyright (c) 2015 Arnaud Levaufre <arnaud@levaufre.name>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import smtplib
import urllib.request
import xmlrpc.client
import logging
from email.mime.text import MIMEText


SMTP_SERVER_IP = ""
SMTP_SEVER_PORT = 587
SMTP_SERVER_LOGIN = ""
SMTP_SERVER_PASSwORD = ""

IP_GETTER_URL = "http://5.39.16.10/tout/ip/"

GANDI_API_URL = "https://rpc.gandi.net/xmlrpc/"
GANDI_API_KEY = ""
GANDI_ZONE_NAME = ""
GANDI_RECORD_NAME = ""

MAIL_FROM = ""
MAIL_TO = ""
MAIL_SUBJECT = "Home's IP address has changed to {ip}"
MAIL_MESSAGE = "Home's IP address has changed to {ip}"

LOG_FORMAT = "%(asctime)s -- %(levelname)s -- %(message)s"
#logging.basicConfig(filename='gandip.log',level=logging.INFO, format=LOG_FORMAT)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


class GandiAPI:
    def __init__(self, url, key):
        self.api = xmlrpc.client.ServerProxy(url)
        self.key = key

    def get_current_record_ip(self, zone_name, record_name):
        return self.get_record(zone_name, record_name).get('value')

    def update_record_ip(self, zone_name, record_name, ip):
        logging.debug('Updating record...')
        zone = self.get_zone(zone_name)
        logging.debug('Zone is %s', zone)

        new_zone_version = self.api.domain.zone.version.new(self.key, zone['id'])
        record = self.get_record(zone_name, record_name, new_zone_version)

        if not record:
            logging.critical('Did not find new record in zone.')
            return False

        logging.debug('New zone version is %s ', new_zone_version)
        logging.debug('New record is %s ', record)
        self.api.domain.zone.record.update(
            self.key,
            zone['id'],
            new_zone_version,
            {'id': record['id']},
            {
                'name': record['name'],
                'type': 'A',
                'value': ip
            }
        )
        self.api.domain.zone.version.set(self.key, zone['id'], new_zone_version)
        return True

    def get_zone(self, zone_name):
        for zone in self.api.domain.zone.list(self.key):
            if zone['name'] == zone_name:
                return zone

    def get_record(self, zone_name, record_name, zone_version=None):
        zone = self.get_zone(zone_name)
        try:
            return self.api.domain.zone.record.list(self.key,
                zone['id'],
                zone_version or zone['version'],
                {'name': record_name}
            )[0]
        except KeyError:
            return {}


def send_mail(from_="", to="", subject="", message=""):
    with smtplib.SMTP(SMTP_SERVER_IP, SMTP_SEVER_PORT) as server:
        server.starttls()
        server.login(SMTP_SERVER_LOGIN, SMTP_SERVER_PASSwORD)
        message = MIMEText(message)
        message['subject'] = subject
        message['from'] = from_
        message['to'] = to
        server.send_message(message)


def get_ip():
    request = urllib.request.urlopen(IP_GETTER_URL)
    return request.read().decode()


if __name__ == "__main__":
    logging.info('Gandi record update started.')

    api = GandiAPI(GANDI_API_URL, GANDI_API_KEY)
    last_ip = api.get_current_record_ip(GANDI_ZONE_NAME, GANDI_RECORD_NAME)
    logging.debug("Current record ip address is %s", last_ip)
    current_ip = get_ip()
    logging.debug("Current ip address is %s", current_ip)

    if current_ip and current_ip != last_ip:
        logging.info("Ip address has changed since last record update. New ip is %s", current_ip)
        api.update_record_ip(
            GANDI_ZONE_NAME,
            GANDI_RECORD_NAME,
            current_ip
        )
        send_mail(
            from_=MAIL_FROM,
            to=MAIL_TO,
            subject=MAIL_SUBJECT.format(ip=current_ip),
            message=MAIL_MESSAGE.format(ip=current_ip)
        )
    else:
        logging.info("Ip address has not changed.")

    logging.info('Gandi record update finished.')

