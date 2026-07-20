#!/usr/bin/env python3
import argparse
import json
import socket
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description='Check d3v-skyman health status')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default='25121', type=int)
    args = parser.parse_args()

    try:
        with socket.create_connection((args.host, args.port), timeout=3) as sock:
            raw = sock.recv(4096).decode('utf-8').strip()
            payload = json.loads(raw)
            print(payload.get('status', 'unknown'))
            return 0
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
