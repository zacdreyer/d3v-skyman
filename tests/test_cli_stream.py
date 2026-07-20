import importlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import types
import unittest

config_module = types.ModuleType("config")
config_module.app = {"debug": 0, "name": "d3v-skyman"}
config_module.module = {"active": {"cli", "app"}}
config_module.encryption = {"key": "0123456789abcdef0123456789abcdef", "iv": "0123456789abcdef"}
config_module.daemon = {"password": "super-secure-password-123", "whitelist": ["127.0.0.1"], "port": 25120}
sys.modules.setdefault("config", config_module)

from modules import app
from modules import cli


class CliStreamTests(unittest.TestCase):
    def test_execute_stream_yields_stdout_chunks(self):
        chunks = list(cli.execute_stream("python3 -c \"print('hello')\""))
        output = "".join(chunks)

        self.assertIn("hello", output)
        self.assertGreater(len(chunks), 0)

    def test_execute_stream_rejects_shell_metacharacters(self):
        with self.assertRaises(ValueError):
            list(cli.execute_stream("echo danger && rm -rf /"))

    def test_client_communication_falls_back_when_crypto_package_is_incompatible(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        crypto_module = types.ModuleType("Crypto")
        cipher_module = types.ModuleType("Crypto.Cipher")

        class BrokenAES:
            @staticmethod
            def new(*args, **kwargs):
                raise RuntimeError("unsupported crypto implementation")

        cipher_module.AES = BrokenAES
        crypto_module.Cipher = cipher_module
        sys.modules["Crypto"] = crypto_module
        sys.modules["Crypto.Cipher"] = cipher_module

        sys.modules.pop("d3vskyman", None)
        spec = importlib.util.spec_from_file_location("d3vskyman", os.path.join(repo_root, "d3vskyman.py"))
        d3vskyman = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(d3vskyman)

        comm = d3vskyman.ClientCommunication("0123456789abcdef", "0123456789abcdef")
        ciphertext = comm.encrypt("hello fallback")

        self.assertEqual(comm.decrypt(ciphertext), "hello fallback")

    def test_stop_returns_false_when_no_process_is_running(self):
        original = app.cli.execute
        app.cli.execute = lambda *_args, **_kwargs: ""
        try:
            self.assertFalse(app.stop())
        finally:
            app.cli.execute = original

    def test_update_rejects_invalid_paths(self):
        with self.assertRaises(ValueError):
            app.update("/definitely/not/a/real/path")

    def test_healthcheck_script_reports_status(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        def serve_once():
            conn, _ = server.accept()
            with conn:
                conn.sendall(b'{"status": "ok"}\n')

        threading.Thread(target=serve_once, daemon=True).start()
        result = subprocess.run(
            [sys.executable, os.path.join(repo_root, "healthcheck.py"), "--host", "127.0.0.1", "--port", str(port)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        server.close()

        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout.lower())

    def test_health_server_returns_status_payload(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, repo_root)
        import d3vskyman

        config_module = types.ModuleType("config")
        config_module.app = {"debug": 0, "name": "d3v-skyman"}
        config_module.module = {"active": {"cli", "app"}}
        config_module.encryption = {"key": "0123456789abcdef0123456789abcdef", "iv": "0123456789abcdef"}
        config_module.daemon = {"password": "super-secure-password-123", "whitelist": ["127.0.0.1"], "port": 25120, "health_host": "127.0.0.1", "health_port": 25221}
        sys.modules["config"] = config_module

        d3vskyman.config = config_module

        server_thread = threading.Thread(target=d3vskyman._run_health_server, daemon=True)
        server_thread.start()

        for _ in range(20):
            try:
                with socket.create_connection(("127.0.0.1", 25221), timeout=0.2) as sock:
                    payload = sock.recv(4096).decode("utf-8").strip()
                    data = json.loads(payload)
                    self.assertEqual(data["status"], "ok")
                    break
            except OSError:
                continue
        else:
            self.fail("health server did not respond")


if __name__ == "__main__":
    unittest.main()
