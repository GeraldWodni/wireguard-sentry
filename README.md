# wireguard-sentry
Peer-server switcher for multi-hub-spoke model wireguard networks

## Motivation
Ever tried to have many clients in a wireguard network using a single server? Easy, lots of tutorials!
What about making that redundant with multiple servers and many clients? Oh wow - what a mess :(

Well traveller, you found a repo which fixes that issue!

## Functionality
This script checks each of your servers in an ordered list. If the first one goes offline, it will switch to the next one and so on.
Should the first become reachable again, it will switch back after some hysteresis.

## Usage
Configure your Wireguard with multiple hosts (must be the same order on each host).
Start this script as systemd-process with the wireguard-network-name and enjoy.

## Sources
Haven't done python since a long time, this is the first time I am using this new fangled-`uv` system.
Well ChatGPT created hot garbage, I do not know how the vibe coders do it, but I found this
[wonderful article](Wonderful tutorial on https://note.nkmk.me/en/python-uv-cli-tool/),
much more helpful than AI-Slop!

Add some hours of conventional brain usage and you got yourself a working project instead of a unmaintanable codebase with a lying agent.

