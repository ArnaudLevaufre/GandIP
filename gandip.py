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
import logging
import argparse
import json

import sys


IP_GETTER_URL = "http://5.39.16.10/tout/ip/"
GANDI_API_URL = "https://dns.api.gandi.net/api/v5"
LOG_FORMAT = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class GandiAPI:
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def update_records(self, fqdn, records, current_ip, ttl=10800):
        all_records = self.get_record_list(fqdn)

        filtered_records = list(filter(
            lambda x: x['rrset_name'] in records and x['rrset_type'] == 'A', all_records
        ))
        has_different_ips = any(list(map(
            lambda x: x['rrset_values'] != [current_ip], filtered_records
        )))

        if has_different_ips:
            for record in filtered_records:
                record["rrset_values"] = [current_ip]
                record["rrset_ttl"] = ttl

                logger.info(
                    "Updating record %s for domain %s with new ip %s",
                    record['rrset_name'],
                    fqdn,
                    current_ip
                )

                name = record["rrset_name"]
                request = urllib.request.Request(
                    f"{self.url}/domains/{fqdn}/records/{name}",
                    method="PUT",
                    headers = {
                        "Content-Type": "application/json",
                        "X-Api-Key": self.key
                    },
                    data=json.dumps({
                        "items": filtered_records
                    }).encode()
                )
                with urllib.request.urlopen(request) as response:
                    logger.debug(json.loads(response.read().decode()))
        else:
            logger.info("Everything is up to date")

        return True

    def get_record_list(self, fqdn):
        request = urllib.request.Request(f"{self.url}/domains/{fqdn}/records")
        request.add_header("X-Api-Key", self.key)
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())


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
    parser.add_argument("--ttl", type=int, default=10800, help="Set a custom ttl (in second)")
    args = parser.parse_args()

    logger.info('Gandi record update started.')

    current_ip = get_current_ip(args.ip_getter)
    api = GandiAPI(GANDI_API_URL, args.key)
    api.update_records(args.zone, args.record, current_ip, ttl=args.ttl)


if __name__ == "__main__":
    main()
