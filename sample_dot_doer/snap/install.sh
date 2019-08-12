#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
pkexec ln -s ./snap_git /var/www/html/snap && chown www-data:www-data -r /var/www/html/
