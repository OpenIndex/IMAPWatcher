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

from threading import Thread
from time import time, sleep

from imapclient import IMAPClient
from imapclient.response_types import Envelope

from . import create_logger
from .callback import CallbackHandler
from .connector import ImapConnector


class ImapIdleHandler:
    """
    Opens an IMAP connections, enters IDLE mode and waits for incoming messages.
    see https://imapclient.readthedocs.io/en/2.3.1/advanced.html#watching-a-mailbox-using-idle
    """

    MAX_IMAP_ERROR_COUNT: int = 0
    """
    Maximum number of errors until an IMAP thread is stopped.
    Set to 0 to run infinitely.
    """

    SECONDS_TO_WAIT_AFTER_ERROR: int = 60
    """
    Number of seconds to wait after an error occurred within the thread.
    """

    SECONDS_TO_RECONNECT_AFTER: int = 600
    """
    Number of seconds after a new IMAP connection is established.
    This is suggested behaviour by the IMAPClient developers.
    see https://imapclient.readthedocs.io/en/2.3.1/advanced.html#watching-a-mailbox-using-idle
    """

    SECONDS_TO_WAIT_FOR_IDLE_RESPONSE: int = 15
    """
    How many seconds the client should for IDLE responses.
    As defined by the IMAP standard, we should not wait for longer than 30 seconds. 
    """

    def __init__(
            self,
            name: str,
            connector: ImapConnector,
            callback: CallbackHandler,
            folder: str = 'INBOX',
            ignoreRecentFlag: bool = False,
    ):
        self.__name = name.strip()
        self.__folder = folder.strip()
        self.__connector = connector
        self.__callback = callback
        self.__ignoreRecentFlag = ignoreRecentFlag
        self.__logger = create_logger(self.__name)

        # Prepare thread.
        self.__thread = Thread(target=self.__idle)
        self.__thread_stopped = False
        self.__connected_at = None
        self.__imap_error_count = 0
        # self.__event = Event()

    def start(self):
        """
        Start the thread.
        """

        self.__thread.start()

    def stop(self):
        """
        Stop the thread.
        """

        self.__thread_stopped = True

    def join(self):
        """
        Join the thread.
        """

        self.__thread.join()

    def __idle(self):
        """
        The m ain thread function initiates an IMAP connection in an endless loop.

        As this application runs infinitely as a service and the target IMAP server might be offline temporarily,
        we want to keep this thread running until the target IMAP server becomes available again.
        """

        while True:
            if self.__thread_stopped:
                self.__logger.info('Thread stopped.')
                break

            try:
                client = self.__connector.connect(
                    select_folder=self.__folder,
                    select_folder_readonly=True
                )
            except Exception as ex:
                self.__logger.exception('Connection failed. %s', str(ex))

                # noinspection DuplicatedCode
                if self.MAX_IMAP_ERROR_COUNT > 0:
                    self.__imap_error_count += 1
                    if self.__imap_error_count > self.MAX_IMAP_ERROR_COUNT:
                        self.__logger.warning('Leaving the thread after %s errors.', self.__imap_error_count)
                        return

                if self.SECONDS_TO_WAIT_AFTER_ERROR > 0:
                    sleep(self.SECONDS_TO_WAIT_AFTER_ERROR)

                # Trying again.
                continue

            try:
                self.__idle_client(client)
            except Exception as ex:
                self.__logger.exception('IDLE failed. %s', str(ex))

                # noinspection DuplicatedCode
                if self.MAX_IMAP_ERROR_COUNT > 0:
                    self.__imap_error_count += 1
                    if self.__imap_error_count > self.MAX_IMAP_ERROR_COUNT:
                        self.__logger.warning('Leaving the thread after %s errors.', self.__imap_error_count)
                        return

                if self.SECONDS_TO_WAIT_AFTER_ERROR > 0:
                    sleep(self.SECONDS_TO_WAIT_AFTER_ERROR)

                # Trying again.
                continue

            finally:
                # noinspection PyBroadException
                try:
                    if client:
                        client.logout()
                except Exception:
                    pass

    def __idle_client(self, client: IMAPClient):
        """
        Puts IMAP client into IDLE mode and waits for server messages in an endless loop.

        As suggested bei the IMAPClient developers, we are closing the IDLE connection after a certain amount of time
        and do a reconnect (https://imapclient.readthedocs.io/en/2.3.1/advanced.html#watching-a-mailbox-using-idle).

        :param client: IMAP client
        """

        if self.__thread_stopped:
            return

        # Start IDLE mode
        try:
            self.__logger.info('Enter IDLE mode.')
            self.__connected_at = int(time())
            client.idle()
        except Exception as ex:
            raise Exception('IDLE mode failed.') from ex

        try:
            # self.__logger.info('Connection is now in IDLE mode.')
            while True:
                if self.__thread_stopped:
                    break

                # Enforce reconnection after 10 minutes.
                if self.SECONDS_TO_RECONNECT_AFTER > 0:
                    age = int(time()) - self.__connected_at
                    if age > self.SECONDS_TO_RECONNECT_AFTER:
                        self.__logger.info('Enforce reconnection.')
                        break

                try:
                    self.__idle_loop(client)
                    self.__imap_error_count = 0
                except KeyboardInterrupt:
                    self.__logger.info('Stopped by keyboard interruption.')
                    self.__thread_stopped = True
                    break
                except Exception as ex:
                    raise Exception('IDLE check failed.') from ex
        finally:
            # noinspection PyBroadException
            try:
                self.__logger.info('Leaving IDLE mode.')
                client.idle_done()
            except Exception:
                pass

    def __idle_loop(self, client: IMAPClient):
        """
        Wait for IDLE responses of the server and process the results.

        :param client: IMAP client
        """

        responses = client.idle_check(timeout=self.SECONDS_TO_WAIT_FOR_IDLE_RESPONSE)
        if not responses:
            return

        self.__logger.info('Received: %s', str(responses))
        message_nr = self.__get_new_message_number(responses, self.__ignoreRecentFlag)
        if not message_nr:
            # self.__logger.info('Ignore message.')
            return

        self.__logger.info('Fetching envelope for message nr %s.', message_nr)
        envelope = self.__get_message_envelope(message_nr)
        if not envelope:
            return

        try:
            self.__callback.trigger_new_message_command(envelope=envelope)
        except Exception as ex:
            self.__logger.exception('Callback failed. %s', str(ex))

    @staticmethod
    def __get_new_message_number(responses, ignoreRecentFlag) -> int | None:
        """
        Extracts the message number fron an IDLE server response.

        Response for new messages should look somehow like
        [(275, b'EXISTS'), (1, b'RECENT')]

        TODO: Not sure, if it is the best possible implementation, maybe the is a better approach.

        :param responses: received IMAP idle responses
        :return: extracted message number or None, if nothing usable found
        """


        if ignoreRecentFlag == False:
            if not (type(responses) is list):
                return None
            if len(responses) < 2:
                return None

            response1 = responses[0]
            if not (type(response1) is tuple):
                return None
            if len(response1) < 2:
                return None

            response2 = responses[1]
            if not (type(response2) is tuple):
                return None
            if len(response2) < 2:
                return None

            if response1[1] == b'EXISTS' and response2[1] == b'RECENT':
                return response1[0]

            if response2[1] == b'EXISTS' and response1[1] == b'RECENT':
                return response2[0]
        else:

            """
            Trigger the script for new messages that look like
            [(275, b'EXISTS'))]
            """

            if not (type(responses) is list):
                return None
            if len(responses) < 1:
                return None

            response1 = responses[0]
            if not (type(response1) is tuple):
                return None
            if len(response1) < 2:
                return None

            if response1[1] == b'EXISTS':
                return response1[0]

        return None

    def __get_message_envelope(self, message_number) -> Envelope | None:
        """
        Get envelope data for a certain message.
        We are using a separate client connection in order to keep the IDLE connection untouched.

        :param message_number: message number to fetch
        :return: message envelope or None, if not found
        """

        client = None
        try:
            client = self.__connector.connect(
                select_folder=self.__folder,
                select_folder_readonly=True
            )

            result = client.fetch([message_number], ['ENVELOPE'])
            if message_number not in result:
                self.__logger.warning('No data found for message nr %s.', message_number)
                return None

            message_result = result[message_number]
            if b'ENVELOPE' not in message_result:
                self.__logger.warning('No envelope data found for message nr %s.', message_number)
                return None

            return message_result[b'ENVELOPE']

        except Exception as ex:
            self.__logger.exception('Separate IMAP connection failed. %s', str(ex))
            return None

        finally:
            # noinspection PyBroadException
            try:
                if client:
                    client.logout()
            except Exception:
                pass
