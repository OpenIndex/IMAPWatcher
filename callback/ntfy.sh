#!/usr/bin/env bash
#
# This is an example callback script, that sends a push notification for each incoming message via ntfy.
#
# PLEASE NOTICE:
# This script won't work out of the box!
# You need to setup your own ntfy server (https://docs.ntfy.sh/install/)
# or get a subscription at ntfy.sh (https://ntfy.sh/#pricing).
#

# ntfy server url
# might also be provided via "env_ntfy_server" in your configuration file
if [[ -z "${NTFY_SERVER}" ]]; then
  NTFY_SERVER="ntfy.sh"
fi

# ntfy auth token
# might also be provided via "env_ntfy_auth_token" in your configuration file
if [[ -z "${NTFY_AUTH_TOKEN}" ]]; then
  NTFY_AUTH_TOKEN="tk_ThisIsAnExampleToken"
fi

# the notification topic depends on the mail account being used
# add "env_ntfy_topic" to your configuration file
if [[ -z "${NTFY_TOPIC}" ]]; then
  echo "The ntfy topic is missing!"
  echo "Please provide a topic via \"env_ntfy_topic\" in your configuration file."
  exit 1
fi

# send push notification via ntfy
# see https://docs.ntfy.sh/publish/
curl \
  -H "Authorization: Bearer ${NTFY_AUTH_TOKEN}" \
  -H "Title: ${MESSAGE_SUBJECT}" \
  -H "Priority: high" \
  -H "Tags: envelope_with_arrow" \
  -d "new mail by ${MESSAGE_AUTHOR}" \
  "${NTFY_SERVER}/${NTFY_TOPIC}"
