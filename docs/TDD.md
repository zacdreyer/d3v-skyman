# Test-Driven Development (TDD) Plan

## 1. Objective

This document captures the current regression-test approach for d3v-skyman. The goal is to make sure authentication, command routing, encryption, service-control behavior, and deployment helpers remain correct as the daemon evolves.

## 2. Current State

The repository now includes an automated Python regression suite in [tests/test_cli_stream.py](../tests/test_cli_stream.py). The suite covers the core daemon behavior and some deployment-oriented safeguards.

## 3. Test Stack

- Python tests: the built-in `unittest` module
- Deployment checks: Python subprocess-based smoke tests for the health-check script

## 4. Current Test Coverage

### Unit Tests

- ClientCommunication.encrypt and ClientCommunication.decrypt round-trip plaintext correctly.
- The fallback encryption path still works when Crypto is unavailable or incompatible.
- modules.cli.execute_stream rejects empty commands, control characters, and disallowed shell metacharacters.
- modules.app.stop returns False when no matching process is running.
- modules.app.update rejects invalid paths.

### Integration / Smoke Tests

- The CLI execution path returns stdout chunks for a simple command.
- The health listener returns a JSON payload containing status ok.
- The health-check script exits successfully when it can read a status payload from the service.

## 5. Test Status

The current test suite is expected to be run with:

- `source .venv/bin/activate`
- `python -m unittest discover -s tests -v`

The latest verified run completed successfully with 7 tests passing and 0 failures.

## 6. TDD Workflow Used Here

1. Add or update a regression test that captures the desired behavior.
2. Run the test to confirm the current implementation does not satisfy it.
3. Implement the minimum code change required to make it pass.
4. Re-run the full suite to ensure the change did not introduce regressions.
5. Refactor carefully while preserving the same contract.

## 7. Definition of Done

A feature is complete when:

- a regression test exists for the behavior
- the behavior is verified by the test suite
- the implementation remains compatible with the existing daemon protocol
- the relevant design note reflects the implemented behavior
