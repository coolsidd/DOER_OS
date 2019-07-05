#!/usr/bin/env bash
/etc/init.d/network-manager start
/etc/init.d/apache2 restart
dbus-uuidgen > /var/lib/dbus/machine-id
mkdir -p /var/run/dbus
dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address
plinth
