#
# Copyright 2023 OpenIndex.de.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import traceback
from datetime import datetime

from imapclient import IMAPClient
from imapclient.response_types import Address, Envelope

from lib import get_envelope_subject, \
    get_envelope_sender_first, \
    get_envelope_from_first, \
    get_envelope_date
from lib.config import get_config, get_imap_folder, create_imap_connector
from lib.connector import ImapConnector

if __name__ == '__main__':
    config = get_config()
    if not config:
        exit(1)

    sections = config.sections()
    if not sections:
        print('No IMAP servers configured. Nothing to do.')
        exit(0)

    for section in sections:
        connector: ImapConnector = create_imap_connector(config=config, section=section)

        print('[%s] Testing connection...' % section)
        client: IMAPClient | None = None
        try:
            folder = get_imap_folder(config=config, section=section)

            try:
                client = connector.connect(
                    select_folder=folder,
                    select_folder_readonly=True,
                )
            except Exception as ex:
                print('[%s] ERROR: Connection failed! %s\n%s' % (
                    section,
                    str(ex),
                    '\n'.join(traceback.format_exception(ex)),
                ))
                continue

            print('[%s] Connection successful.' % section)

            try:
                capabilities = []
                for cap in client.capabilities():
                    capabilities.append(cap.decode('utf-8'))

                print('[%s] Capabilities: %s' % (section, ', '.join(sorted(capabilities)),))
            except Exception as ex:
                print('[%s] ERROR: Can\'t load server capabilities! %s\n%s' % (
                    section,
                    str(ex),
                    '\n'.join(traceback.format_exception(ex)),
                ))
                continue

            print('[%s] Fetch latest message from "%s".' % (section, folder,))
            message_numbers = client.search()
            if len(message_numbers) < 1:
                print('[%s] No messages found in "%s".' % (section, folder,))
                continue

            last_message_number = message_numbers[len(message_numbers) - 1]
            # print('[%s] Fetching message number #%s...' % (section, last_message_number,))

            result = client.fetch([last_message_number], ['ENVELOPE'])
            if last_message_number not in result:
                print('[%s] ERROR: No envelope data found for message nr %s in "%s".' % (
                    section,
                    last_message_number,
                    folder,
                ))
                continue

            print('[%s] Latest message in "%s":' % (section, folder,))

            last_message_envelope: Envelope = result[last_message_number][b'ENVELOPE']
            # pprint(last_message_envelope)

            msg_date: datetime | None = get_envelope_date(last_message_envelope)
            print('-> Date    : %s' % msg_date)

            subject: str | None = get_envelope_subject(last_message_envelope)
            print('-> Subject : %s' % subject)

            from_address: Address | None = get_envelope_from_first(last_message_envelope)
            print('-> From    : %s' % str(from_address))

            sender_address: Address | None = get_envelope_sender_first(last_message_envelope)
            print('-> Sender  : %s' % str(sender_address))

        finally:
            # noinspection PyBroadException
            try:
                if client:
                    client.logout()
            except Exception:
                pass
