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

from lib import create_logger
from lib.callback import CallbackHandler
from lib.config import get_config, \
    create_imap_connector, \
    create_imap_idle_handler, \
    create_callback_handler
from lib.connector import ImapConnector
from lib.idle import ImapIdleHandler

if __name__ == '__main__':
    root_logger = create_logger()

    config = get_config(logger=root_logger)
    if not config:
        exit(1)

    sections = config.sections()
    if not sections:
        root_logger.warning('No IMAP servers configured. Nothing to do.')
        exit(0)

    for section in sections:
        callback: CallbackHandler = create_callback_handler(
            config=config,
            section=section,
        )

        connector: ImapConnector = create_imap_connector(
            config=config,
            section=section,
        )

        handler: ImapIdleHandler = create_imap_idle_handler(
            config=config,
            section=section,
            connector=connector,
            callback=callback,
        )

        handler.start()
        # handler.join()
