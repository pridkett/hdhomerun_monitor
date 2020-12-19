#!/usr/bin/python

import argparse
import csv
import re
import os
from typing import List
from subprocess import Popen, PIPE
import time

NUM_TUNERS = 2
SCAN_DURATION = 30
LOCK_DELAY = 2

scan_regex = re.compile("^SCANNING: [0-9]+ \((?P<freqtable>[a-z-]+):(?P<freq>[0-9]+)\)$")
lock_regex = re.compile("^LOCK: (?P<lock>[0-9a-z]+) \(ss=(?P<ss>[0-9]+) snq=(?P<snq>[0-9]+) seq=(?P<seq>[0-9]+)\)$")
status_regex = re.compile("^ch=(?P<freqtable>[a-z-]+):(?P<freq>[0-9]+) lock=(?P<lock>[0-9a-z]+) ss=(?P<ss>[0-9]+) snq=(?P<snq>[0-9]+) seq=(?P<seq>[0-9]+) bps=(?P<bps>[0-9]+) pps=(?P<pps>[0-9]+)$")

def scan_channels(hdhr: str, freqs: List[int], outfile: str):
    freq_ctr = 0

    mode = 'w'
    if os.path.exists(outfile):
        mode = 'a+'
    with open(outfile, mode, newline='') as csvfile:
        fieldnames = ['time', 'freq', 'lock', 'ss', 'snq', 'seq', 'bps', 'pps']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        if mode is not 'a+':
            writer.writeheader()

        while True:
            scan_freqs = (freqs+freqs)[freq_ctr:freq_ctr + NUM_TUNERS]
            freq_ctr = (freq_ctr + NUM_TUNERS)%len(freqs)
            start_time = time.time()

            # tune to the frequencies
            for tuner_id in range(NUM_TUNERS):
                cmd = ['hdhomerun_config', hdhr, 'set', f'/tuner{tuner_id}/channel', f'auto:{scan_freqs[tuner_id]}']
                Popen(cmd, shell=False, bufsize=1, stdout=PIPE) 

            # monitor the frequencies
            while time.time() < start_time + SCAN_DURATION:
                if time.time() > start_time + LOCK_DELAY:
                    for tuner_id in range(NUM_TUNERS):
                        cmd = ["hdhomerun_config", hdhr, "get", f'/tuner{tuner_id}/status']
                        proc = Popen(cmd, shell=False, bufsize=1, stdout=PIPE) 
                        if proc is not None and proc.stdout is not None:
                            status_result = status_regex.match([x.decode('utf-8').strip() for x in proc.stdout.readlines()][0])
                            if status_result is not None:
                                print(f'channel: {status_result.group("freq")}')
                                writer.writerow({**status_result.groupdict(), **{'time': int(time.time())}})
                        else:
                            raise Exception("comand output was None")
                csvfile.flush()
                time.sleep(1)

def get_scanned_frequencies(scanfile: str) -> List[int]:
    frequencies = []
    with open(scanfile) as f:
        lines = [x.strip() for x in f.readlines()]
        linenum = 0
        while linenum < len(lines):
            scan_result = None
            lock_result = None
            while scan_result == None:
                scan_result = scan_regex.match(lines[linenum])
                linenum = linenum + 1
            while lock_result == None:
                lock_result = lock_regex.match(lines[linenum])
                linenum = linenum + 1
            if lock_result is not None and scan_result is not None and lock_result.group('lock') != 'none':
                frequencies.append(int(scan_result.group('freq')))
                print(f'frequency: {scan_result.group("freq")} lock: {lock_result.group("lock")}')
    return frequencies

def get_hdhr_id() -> str:
    cmd = ["hdhomerun_config", "discover"]
    proc = Popen(cmd, shell=False, bufsize=1, stdout=PIPE)
    if proc is not None and proc.stdout is not None:
        out = [x.decode('utf-8') for x in proc.stdout.readlines()]
    else:
        raise Exception(f'uncaught error invoking: {" ".join(cmd)}')
    return out[0].split()[2]

def main(scanfile: str, outfile: str):
    hdhr_id = get_hdhr_id()
    freqs = get_scanned_frequencies(scanfile)
    scan_channels(hdhr_id, freqs, outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='scanfile', help='the file with the output of the scan')
    parser.add_argument(dest='outfile', help='output file to write CSV to')

    args = parser.parse_args()
    main(scanfile=args.scanfile, outfile=args.outfile)
