#!/bin/bash

mkdir -p "$HOME/tmp"
PIDFILE="$HOME/tmp/myprogram.pid"

if [ -e "${PIDFILE}" ] && (ps -u $(whoami) -opid= |
                           grep -P "^\s*$(cat ${PIDFILE})$" &> /dev/null); then
  echo "Already running."
  exit 99
fi

python crawler  > $HOME/tmp/myprogram.log &

echo $! > "${PIDFILE}"
chmod 644 "${PIDFILE}"

