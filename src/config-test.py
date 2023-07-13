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

from datetime import datetime

from imapclient import IMAPClient
from imapclient.response_types import Address, Envelope

from lib import get_envelope_subject, \
    get_envelope_sender_first, \
    get_envelope_from_first, \
    get_envelope_date, \
    create_logger
from lib.config import get_config, get_imap_folder, create_imap_connector
from lib.connector import ImapConnector

if __name__ == '__main__':
    root_logger = create_logger()

    config = get_config(logger=root_logger)
    if not config:
        exit(1)

    sections = config.sections()
    if not sections:
        root_logger.warning('No IMAP servers configured. Nothing to do.')
        exit(0)

    root_logger.info('Testing %s configured IMAP connections...', len(sections))
    for section in sections:
        logger = create_logger(section)

        try:
            connector: ImapConnector = create_imap_connector(config=config, section=section)
        except Exception as ex:
            logger.exception('Invalid configuration. %s', str(ex))
            continue

        logger.info('Testing connection...')
        client: IMAPClient | None = None
        try:
            folder = get_imap_folder(config=config, section=section)

            try:
                client = connector.connect(
                    select_folder=folder,
                    select_folder_readonly=True,
                )
            except Exception as ex:
                logger.exception('Connection failed. %s', str(ex))
                continue

            logger.info('Connection successful.')

            try:
                capabilities = []
                for cap in client.capabilities():
                    capabilities.append(cap.decode('utf-8'))

                logger.info('Capabilities: %s', ', '.join(sorted(capabilities)))
            except Exception as ex:
                logger.exception('Can\'t load server capabilities. %s', str(ex))
                continue

            logger.info('Fetch latest message from "%s".', folder)
            message_numbers = client.search()
            if len(message_numbers) < 1:
                logger.info('No messages found in "%s".', folder)
                continue

            last_message_number = message_numbers[len(message_numbers) - 1]
            result = client.fetch([last_message_number], ['ENVELOPE'])
            if last_message_number not in result:
                logger.error('No envelope data found for message nr %s in "%s".', last_message_number, folder)
                continue

            message_info = ['Latest message in "%s":' % folder]

            last_message_envelope: Envelope = result[last_message_number][b'ENVELOPE']

            msg_date: datetime | None = get_envelope_date(last_message_envelope)
            message_info.append('-> Date    : %s' % msg_date)

            subject: str | None = get_envelope_subject(last_message_envelope)
            message_info.append('-> Subject : %s' % subject)

            from_address: Address | None = get_envelope_from_first(last_message_envelope)
            message_info.append('-> From    : %s' % str(from_address))

            sender_address: Address | None = get_envelope_sender_first(last_message_envelope)
            message_info.append('-> Sender  : %s' % str(sender_address))

            logger.info('\n'.join(message_info))

        finally:
            # noinspection PyBroadException
            try:
                if client:
                    client.logout()
            except Exception:
                pass
