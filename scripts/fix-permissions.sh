#! /bin/bash
cd /srv/
sudo find -type d -exec chmod 6770 "{}" \;
sudo find -type f -exec chmod 660 "{}" \;
