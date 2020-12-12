# hdhomerun_monitor

Patrick Wagstrom &lt;patrick@wagstrom.net&gt;

December 2020

## Overview

This is a really simple script that is intended for monitoring the signal strength on your [HDHomerun](https://www.silicondust.com/) over time. I designed it because I wanted empirical data about the effectiveness of pointing my over-the-air antenna in various directions and tuning the power on my signal amplifier.

## Design Philosophy

I spent some time trying to natively interface with the HDHomerun using python bindings to libhdhomerun and then writing some C/C++ code, but in reality that was probably too much an investment for what I needed to do. Instead, this script now just shells out `hdhomerun_config` to control the device. This also means that the script is rather fragile.

## Usage

Before starting the script, make sure to do a scan and save it to a file. This is desirable because as you point the antenna in different directions and change amplifier strength, the channel scan will differ. Working with a stable and most optimistic channel scan is the best way to handle this.

The following steps will get you the scan file:

```bash
hdhomerun_config discover
hdhomerun_config <YOUR_DEVICE_ID> scan 0 scan.txt
```

This first command should report back something like:

    hdhomerun device 10AABB01 found at 192.168.1.20

That 8 digit hex number is the ID that you'll want to paste in and use as `<YOUR_DEVICE_ID>` in the steps above. When you're done you'll have a file called `scan.txt` that should have a bunch of data that looks somewhat like this:

```
SCANNING: 551000000 (us-bcast:27)
LOCK: none (ss=55 snq=0 seq=0)
SCANNING: 545000000 (us-bcast:26)
LOCK: 8vsb (ss=100 snq=90 seq=100)
TSID: 0x056B
PROGRAM 3: 40.2 FOX6-HD
PROGRAM 4: 40.1 ABC40HD
PROGRAM 5: 40.3 COURTTV
```

If it looks somewhat like that, you should be okay to move to the actual scanning step, which is done by passing in the name of the scan file and location for saving the output CSV:

```
python3 hdhomerun_monitor.py scan.txt scan_output.csv
```

This will run through all of the channels that showed locks in the scan and tune them for 30 seconds at a time. If you've got multiple tuners it will use multiple tuners to accomplish this.

## TODO

* Document how to do the analysis using the jupyter notebook
