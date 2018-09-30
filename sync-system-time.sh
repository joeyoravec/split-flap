#!/bin/bash
sudo /etc/init.d/ ntp stop
sudo ntpdate 0.us.pool.ntp.org
sudo /etc/init.d/ntp start

