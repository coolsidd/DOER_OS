#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
pkexec ln -s ./turtleblock_git /var/www/html/turtleblocks && chown www-data:www-data -r /var/www/html/
