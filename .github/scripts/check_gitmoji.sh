#!/bin/sh
set -e
msg=$(git log -1 --pretty=%s)
if echo "$msg" | grep -Eq '^:[^ ]+: '; then
  echo "gitmoji detected in commit message"
  exit 0
else
  echo "No gitmoji found in commit message"
  echo "Commit message: $msg"
  exit 1
fi
