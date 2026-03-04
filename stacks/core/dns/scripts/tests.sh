#!/bin/bash
# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

set -euo pipefail
IFS=$'\n\t'

# Enable `set -x` when DEBUG=1 to help debugging CI failures locally
if [[ "${DEBUG:-}" == "1" ]]; then
  set -x
fi

# Print a helpful message when a command fails (shows command, exit code and line)
trap 'rc=$?; echo "ERROR: command \"$BASH_COMMAND\" failed with exit $rc at line $LINENO" >&2; exit $rc' ERR

ok() {
  printf "✅ OK: %s\n" "$*"
}

fail() {
  printf "❌ NOK: %s\n" "$*" >&2
  exit 1
}

echo -e "Running dns service tests...\n"

echo "Coredns - Check DNSSEC Settings"
if drill @${DNS_HOST} -p ${DNS_PORT} sigfail.verteiltesysteme.net 2>&1 | grep -q "rcode: SERVFAIL"; then
	ok "rcode: SERVFAIL found"
else
	fail "expected 'rcode: SERVFAIL' but it was not found"
fi
