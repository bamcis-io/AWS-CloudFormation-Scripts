#!/bin/sh

SQUID=$(/usr/bin/which squid)

if [ ! -z "${SQUID_CONFIG}" ]; then
    echo "Writing squid config from environment variable."
    mkdir -p /etc/squid
    echo "${SQUID_CONFIG}" > /etc/squid/squid.conf
else
    echo "No squid config found from environment variable, using default."
fi

echo "Squid config:"
cat /etc/squid/squid.conf
echo ""

if [ ! -z "${FILTER_LOGS}" ] && [ "${FILTER_LOGS}" == "true" ]; then
    echo "Filtering logs against health checks."
    tail -vn 0 -F /var/log/squid/access.log | grep -v "error:invalid-request\|error:transaction-end-before-headers" &
else
    tail -vn 0 -F /var/log/squid/access.log &
fi

echo "Starting squid..."
# -C Do not catch fatal signals.
# -d level Write debugging to stderr also.
# -N No daemon mode.
# -Y Only return UDP_HIT or UDP_MISS_NOFETCH during fast reload.
exec "$SQUID" -NYCd 1 -f /etc/squid/squid.conf