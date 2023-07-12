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

import subprocess
import traceback
from datetime import datetime
from os import getcwd
from threading import Thread

from imapclient.response_types import Envelope, Address

from . import get_envelope_message_id, \
    get_envelope_in_reply_to, \
    get_envelope_date, \
    get_envelope_subject, \
    get_envelope_from_first, \
    get_envelope_sender_first, \
    get_envelope_to_first, \
    get_address_name, \
    get_address_mail


class CallbackHandler:
    """
    Runs an IMAP IDLE callback operations in a separate thread.
    """

    def __init__(
            self,
            name: str,
            on_new_message: str | None = None,
            additional_env: dict | None = None,
    ):
        self.__name = name.strip()
        self.__on_new_message = on_new_message
        self.__additional_env = {**additional_env} if additional_env else {}

    def trigger_new_message_command(self, envelope: Envelope):
        if not self.__on_new_message:
            raise Exception('No command for new message configured.')

        msg_id: str | None = get_envelope_message_id(envelope)
        msg_reply_to_id: str | None = get_envelope_in_reply_to(envelope)
        msg_date: datetime | None = get_envelope_date(envelope)
        msg_subject: str | None = get_envelope_subject(envelope)

        msg_from: Address | None = get_envelope_from_first(envelope)
        msg_from_name = get_address_name(msg_from) if msg_from and msg_from.name else ''
        msg_from_mail = get_address_mail(msg_from) if msg_from and msg_from.host and msg_from.mailbox else ''

        msg_sender: Address | None = get_envelope_sender_first(envelope)
        msg_sender_name = get_address_name(msg_sender) if msg_sender and msg_sender.name else ''
        msg_sender_mail = get_address_mail(msg_sender) if msg_sender and msg_sender.host and msg_sender.mailbox else ''

        msg_to: Address | None = get_envelope_to_first(envelope)
        msg_to_name = get_address_name(msg_to) if msg_to and msg_to.name else ''
        msg_to_mail = get_address_mail(msg_to) if msg_to and msg_to.host and msg_to.mailbox else ''

        msg_author = msg_from if msg_from else msg_sender
        msg_author_name = get_address_name(msg_author) if msg_author and msg_author.name else ''
        msg_author_mail = get_address_mail(msg_author) if msg_author and msg_author.host and msg_author.mailbox else ''

        environment = {
            **self.__additional_env,
            'MESSAGE_ID': str(msg_id) if msg_id else '',
            'MESSAGE_REPLY_TO_ID': str(msg_reply_to_id) if msg_reply_to_id else '',
            'MESSAGE_DATE': str(msg_date) if msg_date else '',
            'MESSAGE_SUBJECT': msg_subject.strip() if msg_subject else '',
            'MESSAGE_AUTHOR': str(msg_author) if msg_author else '',
            'MESSAGE_AUTHOR_NAME': msg_author_name,
            'MESSAGE_AUTHOR_MAIL': msg_author_mail,
            'MESSAGE_FROM': str(msg_from) if msg_from else '',
            'MESSAGE_FROM_NAME': msg_from_name,
            'MESSAGE_FROM_MAIL': msg_from_mail,
            'MESSAGE_SENDER': str(msg_sender) if msg_sender else '',
            'MESSAGE_SENDER_NAME': msg_sender_name,
            'MESSAGE_SENDER_MAIL': msg_sender_mail,
            'MESSAGE_TO': str(msg_to) if msg_to else '',
            'MESSAGE_TO_NAME': msg_to_name,
            'MESSAGE_TO_MAIL': msg_to_mail,
        }

        CallbackThread(
            name=self.__name,
            command=self.__on_new_message,
            environment=environment,
        ).start()


class CallbackThread:
    """
    Thread for callback commands.
    """

    def __init__(
            self,
            name: str,
            command: str,
            environment: dict,
    ):
        self.__name = name.strip()
        self.__command = command
        self.__environment = {**environment}
        self.__thread = Thread(target=self.__run)

    def start(self):
        """
        Start the thread.
        """

        self.__thread.start()

    def join(self):
        """
        Join the thread.
        """

        self.__thread.join()

    def __run(self):
        """
        Run a shell command with  provided environment variables.
        """

        try:
            print('[%s] Running "%s" from working directory "%s"...' % (
                self.__name,
                self.__command,
                getcwd(),
            ))

            result: subprocess.CompletedProcess = subprocess.run(
                self.__command,
                shell=True,
                env=self.__environment,
                cwd=getcwd(),
                text=True
            )

            if result.returncode != 0:
                print('[%s] ERROR: Callback script "%s" returned non-zero exit code (%s)!' % (
                    self.__name,
                    self.__command,
                    result.returncode,
                ))
                return

        except Exception as ex:
            print('[%s] ERROR: Callback script error! %s\n%s' % (
                self.__name,
                str(ex),
                '\n'.join(traceback.format_exception(ex)),
            ))
