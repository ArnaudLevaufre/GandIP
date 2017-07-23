# GandIP

Keep you gandi DNS records up to date with your current ip.

## Installation

Easy peasy, run `python setup.py install --user` and create a cron job so it runs every 15 minutes like so:

```
*/15 * * * * gandip your_gandi_api_key zone_name record1 record2 ... recordN
```
