# IMAP Watcher

This application watches one or more IMAP accounts for incoming messages
via [IMAP IDLE](https://en.wikipedia.org/wiki/IMAP_IDLE). In case a new message is received, it triggers an external
script, that might do further actions.

For example we are using this application, to send push notifications via [ntfy](https://ntfy.sh/) in case of incoming
messages. The example callback script [`callback/ntfy.sh`](callback/ntfy.sh) illustrates, how to send those push
notifications for incoming emails.


## How to install

Make sure, you have **Python 3** and **virtualenv** installed. Clone the repository, enter the repository root and
run `init.sh` to download all dependencies.

```bash
git clone https://github.com/OpenIndex/IMAPWatcher.git
cd IMAPWatcher
./init.sh
```

## How to configure

Take a look at [`config.example.ini`](config.example.ini). It describes all available configuration options. Just copy
the example file to any location you like and make your changes.

You might setup **as many IMAP accounts** as you like within one configuration file.


## How to setup the callback script

In your `config.ini` you should provide for each mail account a callback script, that is called for each newly received
message - e.g. the example script

```ini
on_new_message = ./callback/printenv.sh
```

can be used to see all passed environment variables.

These environment variables with informations about the incoming message are passed to the callback script:

| variable              | example value                 | description                                         |
|-----------------------|-------------------------------|-----------------------------------------------------|
| `MESSAGE_ID`          | <123@example.com>             | `Message-Id` header value                           |
| `MESSAGE_REPLY_TO_ID` | <122@example.com>             | `In-Reply-To` header value                          |
| `MESSAGE_DATE`        | 2023-07-12 23:31:07           | message date                                        |
| `MESSAGE_SENDER`      | John Doe <john@example.com>   | complete `Sender` header value                      |
| `MESSAGE_SENDER_NAME` | John Doe                      | name part of `Sender` header value                  |
| `MESSAGE_SENDER_MAIL` | john@example.com              | mail part of `Sender` header value                  |
| `MESSAGE_FROM`        | John Doe <john@example.com>   | complete `From` header value                        |
| `MESSAGE_FROM_NAME`   | John Doe                      | name part of `From` header value                    |
| `MESSAGE_FROM_MAIL`   | john@example.com              | mail part of `From` header value                    |
| `MESSAGE_AUTHOR`      | John Doe <john@example.com>   | either `MESSAGE_FROM` or `MESSAGE_SENDER`           |
| `MESSAGE_AUTHOR_NAME` | John Doe                      | either `MESSAGE_FROM_NAME` or `MESSAGE_SENDER_NAME` |
| `MESSAGE_AUTHOR_MAIL` | john@example.com              | either `MESSAGE_FROM_MAIL` or `MESSAGE_SENDER_MAIL` |
| `MESSAGE_TO`          | Frank Doe <frank@example.com> | complete `To` header value                          |
| `MESSAGE_TO_NAME`     | Frank Doe                     | name part of `To` header value                      |
| `MESSAGE_TO_MAIL`     | frank@example.com             | mail part of `To` header value                      |

The variables `MESSAGE_AUTHOR`, `MESSAGE_AUTHOR_NAME` and `MESSAGE_AUTHOR_MAIL` are some kind of special. By default
they contain the `From` header value. But if the `From` header is not present, the `Sender` header value is used
instead.

Also you might pass additional environment variables to the callback script - e.g. if the mail account in config.ini
contains

```ini
env_additional_variable = test1
env_another_additional_variable = test2
```

also the following environment variables are passed:

```bash
ADDITIONAL_VARIABLE=test1
ANOTHER_ADDITIONAL_VARIABLE=test2
```

Take a look at [`callback/ntfy.sh`](callback/ntfy.sh) as an example, how to send push notifications for incoming email
messages (via [ntfy](https://ntfy.sh/)) by using some of the provided environment variables.


## How to run

Assuming your configuration file is called `config.ini`, you might test the settings first via:

```bash
./run-config-test.sh config.ini
```

If connection to all configured IMAP accounts was successful, you can run IMAP Watcher via:

```bash
./run.sh config.ini
```

For a first test of the callback mechanism you should run the application in foreground and send a test mail to your
configured account.

If the callback mechanism works as expected, feel free to setup a cronjob or Systemd service.


## FAQ

### Does it work with gmail or other providers using OAuth?

OAuth is currently not supported as we don't need it for our daily work. Feel free to provide a pull request. We also take donations for improvements like that.
