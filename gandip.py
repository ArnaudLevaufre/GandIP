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

import argparse
import json
import logging
import os
import urllib.request


IPV4_PROVIDER_URL = "https://api.ipify.org"
IPV6_PROVIDER_URL = "https://api6.ipify.org"
GANDI_API_URL = "https://dns.api.gandi.net/api/v5"
LOG_FORMAT = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class GandiAPI:
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def update_records(self, fqdn, record_names, current_ip, ttl=10800,
                       rtype="A"):

        for name in record_names:
            record = self.get_domain_record_by_name(fqdn, name, rtype=rtype)
            if record is not None and current_ip in record['rrset_values']:
                logger.info(
                    "Record %s for %s.%s is up to date.",
                    rtype, name, fqdn
                )
            else:
                request = urllib.request.Request(
                    f"{self.url}/domains/{fqdn}/records/{name}/{rtype}",
                    method="POST" if record is None else "PUT",
                    headers={
                        "Content-Type": "application/json",
                        "X-Api-Key": self.key
                    },
                    data=json.dumps({
                        "rrset_ttl": ttl,
                        "rrset_values": [current_ip],
                    }).encode()
                )
                with urllib.request.urlopen(request) as response:
                    logger.debug(json.loads(response.read().decode()))
                logger.info(
                    "Record %s for %s.%s is set to %s.",
                    rtype, name, fqdn, current_ip
                )

    def get_domain_record_by_name(self, fqdn, name, rtype="A"):
        try:
            request = urllib.request.Request(
                f"{self.url}/domains/{fqdn}/records/{name}/{rtype}"
            )
            request.add_header("X-Api-Key", self.key)
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError:
            return None


def get_current_ip(provider_url):
    with urllib.request.urlopen(provider_url) as response:
        return response.read().decode()


def main():
    parser = argparse.ArgumentParser(
        description=""""
            Keep your gandi DNS records up to date with your current IP
        """
    )
    parser.add_argument('key', type=str, help="Gandi API key or path to a file containing the key.")
    parser.add_argument('zone', type=str, help="Zone to update")
    parser.add_argument('record', type=str, nargs='+', help="Records to update")
    parser.add_argument("--ttl", type=int, default=10800, help="Set a custom ttl (in second)")
    parser.add_argument("--noipv4", action="store_true", help="Do not set 'A' records to current ipv4")
    parser.add_argument("--noipv6", action="store_true", help="Do not set 'AAAA' records to current ipv6")
    args = parser.parse_args()

    logger.info('Gandi record update started.')

    if os.path.isfile(args.key):
        with open(args.key) as fle:
            gandi_api_key = fle.read().strip()
    else:
        gandi_api_key = args.key

    api = GandiAPI(GANDI_API_URL, gandi_api_key)

    if not args.noipv4:
        current_ipv4 = get_current_ip(IPV4_PROVIDER_URL)
        api.update_records(args.zone, args.record, current_ipv4, ttl=args.ttl)
    if not args.noipv6:
        current_ipv6 = get_current_ip(IPV6_PROVIDER_URL)
        api.update_records(
            args.zone, args.record, current_ipv6, ttl=args.ttl, rtype="AAAA"
        )


if __name__ == "__main__":
    main()
