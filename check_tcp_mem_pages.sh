#!/bin/bash

ALARM_FREE_PAGE_VALUE=$1

do_help(){
        cat <<EOF
script for check tcp_memory pages
        usage: $0 ALARM_VALUE_PAGES 
EOF
        exit 1
}

if [[ -z $1 ]]; then
        do_help
fi

LIMIT_TCP_MEM=$(  cat /proc/sys/net/ipv4/tcp_mem|cut -f 3 )
CURRENT_USAGE_TCP_MEM=$(  cat /proc/net/sockstat|grep TCP|grep -Eo 'mem.*'|cut -f 2 -d ' ' )

FREE_MEM_PAGE=`expr $LIMIT_TCP_MEM - $CURRENT_USAGE_TCP_MEM`

if [ "$FREE_MEM_PAGE" -lt "$ALARM_FREE_PAGE_VALUE" ]; then
        echo "Lower count free tcp memory pages: ${CURRENT_USAGE_TCP_MEM}"      
        exit 1
fi

