"""

Copyright (c) 2017 Arnaud Levaufre <arnaud@levaufre.name>

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

import urllib.request
import xmlrpc.client
import logging
import argparse


IP_GETTER_URL = "http://5.39.16.10/tout/ip/"
GANDI_API_URL = "https://rpc.gandi.net/xmlrpc/"
LOG_FORMAT = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class GandiAPI:
    def __init__(self, url, key):
        self.api = xmlrpc.client.ServerProxy(url)
        self.key = key

    def get_current_record_ip(self, zone_name, record_name):
        return self.get_record(zone_name, record_name).get('value')

    def update_records(self, zone_name, records, current_ip):
        zone = self.get_zone(zone_name)

        all_records = self.api.domain.zone.record.list(
            self.key,
            zone['id'],
            zone['version'],
        )
        filtered_records = list(filter(
            lambda x: x['name'] in records, all_records
        ))
        has_different_ips = any(list(map(
            lambda x: x['value'] != current_ip, filtered_records
        )))

        if has_different_ips:
            new_zone_version = self.api.domain.zone.version.new(self.key, zone['id'])
            for record in filtered_records:
                record = self.get_record(zone['name'], record['name'], new_zone_version)
                self.api.domain.zone.record.update(
                    self.key,
                    zone['id'],
                    new_zone_version,
                    {'id': record['id']},
                    {
                        'name': record['name'],
                        'type': 'A',
                        'value': current_ip
                    }
                )
                logger.info(
                    "Updating record %s in zone %s with new ip %s",
                    record['name'],
                    zone['name'],
                    current_ip
                )
            self.api.domain.zone.version.set(self.key, zone['id'], new_zone_version)
        else:
            logger.info("Everything is up to date")

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
        except IndexError:
            return {}


def get_current_ip(provider_url=IP_GETTER_URL):
    request = urllib.request.urlopen(provider_url)
    return request.read().decode()


def main():
    parser = argparse.ArgumentParser(
        description=""""
            Keep your gandi DNS records up to date with your current IP
        """
    )
    parser.add_argument('key', type=str, help="Gandi API key")
    parser.add_argument('zone', type=str, help="Zone to update")
    parser.add_argument('record', type=str, nargs='+', help="Records to update")
    parser.add_argument("--ip-getter", type=str, default=IP_GETTER_URL, help="""
        Web page that give your current ip. It should only return the ip as
        text. Defaults to {}
    """.format(IP_GETTER_URL))
    args = parser.parse_args()

    logger.info('Gandi record update started.')

    current_ip = get_current_ip(args.ip_getter)
    api = GandiAPI(GANDI_API_URL, args.key)
    api.update_records(args.zone, args.record, current_ip)

if __name__ == "__main__":
    main()
