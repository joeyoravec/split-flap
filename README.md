# split-flap
This project implements controls for the Split-Flap clock available on
thingiverse: https://www.thingiverse.com/thing:2773612

Download RpiMotorLib from https://github.com/gavinlyonsrepo/RpiMotorLib and
put it into the same folder as this python script

Invoke the python app like:

```
# Nudge the motor a few steps forward
$ split-flap.py nudge --motor hour

# Move the motor from current to desired time
$ split-flap.py set_time --current 12:00 --desired 1:30
```

To get run sfc.py to run on power up, add the split-flap.service script into /etc/systemd/system/ directory and run the following commands:

	sudo systemctl daemon-reload
	sudo systemctl enable split-flap.service

Will also need to add network credentials to '/etc/wpa_supplicant/wpa_supplicant.conf'
Reference on setting up wifi - https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md


#Info about writing/running python script on startup (using a .service script)
Reference project - https://github.com/joeyoravec/proton-pack/wiki
https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/sect-managing_services_with_systemd-unit_files

#Synchronizing Linux time - NTP
installing - https://www.tecmint.com/synchronize-time-with-ntp-in-linux/
http://doc.ntp.org/4.1.1/ntpdate.htm

https://www.pool.ntp.org/zone/us

http://earthsky.org/astronomy-essentials/universal-time

current_time.txt - reflects and backs up the time on the physical clock every minute so that the clock can reinitialize after being powered off.

sync-system-time.sh - uses ntp to synchronize linux time

split-flap.log - file that gets created (if not already existing) for logging
