# d3v-skyman

d3v-skyman is a lightweight Python daemon for remote service administration over a TCP socket. It accepts encrypted commands from authenticated clients, executes shell commands, and can stop or update the local service process.

## What the application does

The server listens for incoming connections, verifies the client IP against a whitelist, requires authentication with a password, and then allows command execution through two command families:

- `CLI <command>` for running shell commands
- `APP stop` or `APP update` for service control actions

The server uses AES-CBC encryption to protect the payloads between the client and daemon, and it can optionally expose a local health check endpoint plus TLS if certificate files are configured.

## Project structure

- [d3vskyman.py](d3vskyman.py) - main daemon entry point and socket server loop
- [modules/cli.py](modules/cli.py) - executes shell commands
- [modules/app.py](modules/app.py) - stops or updates the service
- [clients/PHP](clients/PHP) - sample PHP client implementation
- [clients/csharp](clients/csharp) - sample C# client implementation
- [clients/python](clients/python) - sample Python client implementation
- [clients/javascript](clients/javascript) - sample JavaScript client implementation
- [example.config.py](example.config.py) - example server configuration
- [example.loader.sh](example.loader.sh) - example startup script

## Setup

1. Install Python dependencies:
   - `pip3 install -r requirements.txt`
2. Copy [example.config.py](example.config.py) to `config.py` and fill in the daemon settings, encryption values, and whitelist.
3. Start the daemon with:
   - `python3 d3vskyman.py`
4. Optionally use [example.loader.sh](example.loader.sh) to launch it in the background.

## Command flow

1. A client opens a socket connection to the daemon.
2. The client sends an authentication command such as `AUTH <password>`.
3. After authentication succeeds, the client can send `CLI ...` or `APP ...` commands.
4. The daemon decrypts the command, executes it, and returns an encrypted response.
5. The client disconnects with `EXIT`.

## Documentation

The project now includes dedicated documentation for design and test planning:

- [docs/SDD.md](docs/SDD.md) - software design document for the main daemon
- [docs/TDD.md](docs/TDD.md) - test-driven development plan for the Python application
- [clients/docs/SDD.md](clients/docs/SDD.md) - language-agnostic software design document for client implementations
- [clients/docs/TDD.md](clients/docs/TDD.md) - language-agnostic test-driven development plan for clients

## Notes

This project is still a small, purpose-built tool and is best suited to controlled environments. The current implementation is functional but should be hardened before broader production use, especially around authentication, process management, and transport security.