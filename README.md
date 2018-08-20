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
