# Software Design Document (SDD)

## 1. Purpose

This document describes the current design of d3v-skyman, a lightweight Python daemon for remote administration over a TCP socket. The server accepts encrypted commands from authenticated clients, executes local shell actions, and can stop or update the local service process.

## 2. Scope

The current implementation covers:

- a threaded socket server in [d3vskyman.py](../d3vskyman.py)
- encrypted transport using AES-CBC with a shared key and IV
- authentication against a configured password and IP whitelist
- command execution through [modules/cli.py](../modules/cli.py)
- safe service stop and update operations through [modules/app.py](../modules/app.py)
- sample clients in [clients/PHP](../clients/PHP), [clients/csharp](../clients/csharp), [clients/python](../clients/python), and [clients/javascript](../clients/javascript)
- deployment helpers such as [config_loader.py](../config_loader.py), [healthcheck.py](../healthcheck.py), and [example.loader.sh](../example.loader.sh)

## 3. System Overview

The daemon runs as a long-lived process on a configured TCP port. Clients connect over a socket, authenticate with a password, and then send framed commands. The server decrypts the payload, dispatches it to the appropriate handler, and returns an encrypted response or a stream of response chunks.

## 4. Architecture

### 4.1 Main Components

- Core daemon entry point: [d3vskyman.py](../d3vskyman.py)
  - creates the listening socket
  - accepts incoming client connections
  - starts a thread per client session
  - emits structured logs and exposes a health listener
- Config loader: [config_loader.py](../config_loader.py)
  - loads the active configuration from config.py or example.config.py
  - validates deployment-critical settings before the daemon starts
- Communication layer: ClientCommunication
  - handles AES encryption, decryption, and PKCS7-style padding
- Client session handler: ClientThread
  - validates the source IP against the whitelist
  - performs authentication
  - routes CLI or APP handlers
- CLI module: [modules/cli.py](../modules/cli.py)
  - executes shell commands through subprocess with strict input validation
  - rejects empty commands, control characters, and shell metacharacters
- App module: [modules/app.py](../modules/app.py)
  - stops the service process using TERM signals
  - updates the repository by running git pull in a safe path
- Deployment helpers: [healthcheck.py](../healthcheck.py) and [example.loader.sh](../example.loader.sh)
  - provide operational health checks and supervisor-friendly startup behavior

### 4.2 Runtime Flow

1. The daemon starts and binds to the configured host and port.
2. A client connects.
3. The server checks whether the client IP is allowed.
4. The client must send AUTH <password> before privileged commands can run.
5. Once authenticated, the client can send CLI ... or APP ... commands.
6. The server executes the command, formats a response, and sends it back to the client as encrypted frames.
7. The connection closes when the client sends EXIT or when authentication fails.

## 5. Functional Requirements

### Authentication and Access Control

- Connections from non-whitelisted IP addresses must be rejected.
- Clients must authenticate with AUTH <password> before using privileged commands.
- Failed authentication should terminate the session.

### Command Handling

- CLI <command> executes shell commands and returns streamed output.
- APP stop terminates the running service process gracefully.
- APP update pulls the latest repository changes and then stops the service.
- EXIT closes the client connection cleanly.

### Encryption and Transport

- All command payloads are encrypted before transmission.
- The server uses the configured IV and key from the application config.
- Responses are also encrypted before being returned to the client.
- Optional TLS can be enabled by providing certfile and keyfile in the daemon config.
- A simple health listener returns a JSON status payload for operational checks.

## 6. Configuration Model

The application depends on configuration values from [example.config.py](../example.config.py):

- app name and debug mode
- module activation list
- encryption IV and key
- daemon host, port, password, and whitelist
- optional TLS settings and health listener settings

## 7. Design Decisions

- The daemon uses Python threads so each client session can be handled independently.
- The implementation uses AES-CBC for confidentiality and a framed message format for reliability.
- CLI execution is intentionally narrow and safe: command strings are parsed with shlex and rejected if they contain control characters or shell metacharacters.
- The app module relies on the CLI module for the underlying command execution path, keeping shell handling centralized.
- A shared config loader validates required settings before the daemon starts, reducing the chance of insecure or incomplete deployments.

## 8. Non-Functional Requirements

- The daemon should be easy to deploy on a Linux-style host using Python 3.
- The implementation should remain maintainable for small-scale infrastructure tasks.
- The design is now more suitable for controlled production-like environments because it includes validation, logging, health checks, and safer process control.

## 9. Risks and Observations

- The AES implementation still includes a fallback path for environments without a usable Crypto package. That fallback is acceptable for local development and testing, but production deployments should use a real cryptography package and TLS for strong transport security.
- The current protocol remains a lightweight custom socket protocol and does not replace a full service mesh or zero-trust network boundary.
- The sample clients mirror the server protocol and depend on matching encryption settings and passwords.

## 10. Extension Points

The design can be extended by:

- adding new command families beyond CLI and APP
- introducing role-based authorization or per-user access control
- replacing the current custom socket protocol with a more formal broker or RPC layer
- adding stronger operational monitoring, alerting, and secret management
