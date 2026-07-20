# Client Software Design Document (SDD)

## 1. Purpose

This document provides a language-agnostic design guide for clients that connect to the d3v-skyman daemon. The repository now includes reference implementations in Python, PHP, C#, and JavaScript.

## 2. Scope

A client implementation should cover:

- opening a TCP socket to the daemon
- authenticating with the configured password
- encrypting outbound payloads with the shared IV and key
- decrypting inbound responses
- sending commands and returning results in a predictable structure
- handling streamed output from long-running commands

## 3. Core Design

A client is composed of three logical layers:

- transport layer
  - creates the socket connection
  - sends framed messages
  - reads one or more server responses
- encryption layer
  - uses the same AES-CBC settings as the daemon
  - pads and unpads payloads consistently
- command layer
  - formats commands such as AUTH ..., CLI ..., or APP ...
  - normalizes responses into a language-specific result object or array

## 4. Required Protocol Behavior

The client must follow the daemon protocol closely:

1. Connect to the configured host and port.
2. Read the initial welcome message from the server.
3. Send an authentication command such as AUTH <password>.
4. Read and verify the authentication response.
5. Send the desired command.
6. Read the streamed response frames until the server sends the end marker.

## 5. Functional Requirements

- The client must connect to the configured socket host and port.
- The client must authenticate before sending privileged commands.
- The client must use the same encryption key and IV as the server.
- The client must preserve streaming behavior for long-running command output.
- The client should surface status, message, result, and optional stream chunks in a consistent format.

## 6. Implementation Notes

- The daemon expects framed messages terminated by a newline character.
- Commands should be sent as encrypted payloads using the shared protocol.
- For streaming output, the client should incrementally collect chunks until it receives the STREAM_END marker.
- The repository now includes working examples for Python, PHP, C#, and JavaScript so the protocol contract can be implemented in multiple languages without changing the core server behavior.

## 7. Risks and Limitations

- A mismatch in encryption settings will prevent communication.
- The protocol assumes a reliable connection and a trusted environment.
- Network latency can affect how quickly streamed output appears to the caller.
- Production deployments should still use TLS and strong secret management rather than relying on the custom framing layer alone.
