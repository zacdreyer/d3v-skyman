# Client Test-Driven Development (TDD) Plan

## 1. Objective

This document defines the language-agnostic TDD expectations for clients that connect to the d3v-skyman daemon. The repository now includes sample implementations in Python, PHP, C#, and JavaScript.

## 2. Test Scope

A client implementation should be tested for:

- connection setup and teardown
- authentication success and failure
- encryption and decryption correctness
- framed message sending and receiving
- streaming output handling
- response formatting and error handling

## 3. Recommended Test Cases

### Transport Tests

- a successful connection returns the initial welcome message
- a failed connection produces a clear error response
- the client can read multiple frames from the server

### Authentication Tests

- sending the correct password results in an authenticated session
- sending the wrong password results in a failure response

### Encryption Tests

- encryption and decryption preserve the original message
- the client can round-trip punctuation and whitespace safely

### Streaming Tests

- a command that emits multiple output chunks produces multiple chunks on the client side
- the client stops collecting output when it receives the stream end marker

### Response Shape Tests

- the client returns a predictable object or structure containing status, message, and result
- errors are surfaced clearly without losing the underlying reason

## 4. TDD Workflow

1. Write a failing test that describes the expected behavior.
2. Implement the smallest fix required to make the test pass.
3. Run the regression suite and confirm the behavior.
4. Refactor carefully while preserving the same contract.

## 5. Definition of Done

A client feature is complete when:

- a test exists for it
- the implementation passes the relevant regression checks
- the existing suite remains green
- the documented protocol behavior remains aligned with the daemon implementation
