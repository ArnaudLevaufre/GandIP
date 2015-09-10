# GandIP

## Description

This script allows you to automatically send an email and update a gandi DNS
zone when your public IP changes.

## Installation

Easy peasy, edit the constants on top of the script. Then setup a cron job to
run the script once in a while like so:

```
*/30 * * * * /bin/python3 /path/to/the/script/gandip.py
```

