GandIP
======

Keep your gandi DNS records up to date with your current ip.

Please note that gandi is migrating to it's new version (v5) with their new
LiveDNS api used by gandip latest version. In order to use gandip with older
gandi api you must use version 1.x.x.

Installation
------------

Easy peasy, run `pip install --user gandip` and create a cron job so it runs every 15 minutes like so:

```
*/15 * * * * gandip your_gandi_api_key fqdn record1 record2 ... recordN
```
