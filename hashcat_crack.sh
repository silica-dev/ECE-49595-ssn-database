#!/usr/bin/env bash
# assumes hashcat is installed
hashcat -m 70000 -a 3 hashfile.txt -D 1 
