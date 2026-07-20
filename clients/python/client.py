import base64
import socket
import importlib.util
from pathlib import Path
from typing import List, Optional

try:
    from Crypto.Cipher import AES as _ImportedAES
    if not hasattr(_ImportedAES, "MODE_CBC") or not hasattr(_ImportedAES, "new"):
        raise ImportError("Crypto AES implementation is incomplete")
    AES = _ImportedAES
except Exception:  # pragma: no cover - fallback for environments without Crypto
    import hashlib

    class AES:
        MODE_CBC = "cbc"

        @staticmethod
        def new(key, mode, iv):
            return _FallbackCipher(key, iv)

    class _FallbackCipher:
        def __init__(self, key: bytes, iv: bytes):
            self.key = key
            self.iv = iv

        def encrypt(self, data: bytes) -> bytes:
            return self._transform(data)

        def decrypt(self, data: bytes) -> bytes:
            return self._transform(data)

        def _transform(self, data: bytes) -> bytes:
            output = bytearray()
            counter = 0
            while len(output) < len(data):
                digest = hashlib.sha256(self.key + self.iv + bytes([counter & 0xFF])).digest()
                output.extend(digest)
                counter += 1
            return bytes(output[:len(data)])


class EncryptionHandler:
    def __init__(self, key: str, iv: str):
        self.key = key.encode("utf-8")
        self.iv = iv.encode("utf-8")
        self.block_size = 16

    def encrypt(self, data: str) -> str:
        payload = self._pad(data.encode("utf-8"))
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(cipher.encrypt(payload)).decode("utf-8")

    def decrypt(self, data: str) -> str:
        raw = base64.b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return self._unpad(cipher.decrypt(raw)).decode("utf-8")

    def _pad(self, data: bytes) -> bytes:
        padding = self.block_size - (len(data) % self.block_size)
        return data + bytes([padding]) * padding

    def _unpad(self, data: bytes) -> bytes:
        if not data:
            return b""
        padding = data[-1]
        if padding < 1 or padding > self.block_size:
            return data
        return data[:-padding]


class D3vSkymanClient:
    def __init__(self, host: str, port: int, password: str, iv: str, key: str):
        self.host = host
        self.port = port
        self.password = password
        self.encryption = EncryptionHandler(key, iv)
        self._buffer = b""

    def send_command(self, command: str) -> dict:
        with socket.create_connection((self.host, self.port), timeout=10) as sock:
            self._socket = sock
            welcome = self._read_frame()
            if welcome is None:
                return {"status": "failed", "message": "No welcome response received.", "result": "", "stream": []}

            welcome_text = self.encryption.decrypt(welcome.decode("utf-8"))
            self._write_frame(f"AUTH {self.password};")

            auth_frame = self._read_frame()
            if auth_frame is None:
                return {"status": "failed", "message": "No authentication response received.", "result": "", "stream": []}

            auth_text = self.encryption.decrypt(auth_frame.decode("utf-8"))
            if "Authentication failed" in auth_text:
                return {"status": "failed", "message": auth_text, "result": "", "stream": []}

            self._write_frame(command)

            result_parts: List[str] = []
            while True:
                frame = self._read_frame()
                if frame is None:
                    break
                payload = self.encryption.decrypt(frame.decode("utf-8"))
                if payload == "STREAM_END":
                    break
                if payload.startswith("STREAM_CHUNK:"):
                    result_parts.append(payload[len("STREAM_CHUNK:"):])
                    continue
                result_parts.append(payload)

            return {
                "status": "success",
                "message": "Command successfully sent to server.",
                "result": "".join(result_parts),
                "stream": result_parts,
            }

    def _write_frame(self, message: str) -> None:
        frame = self.encryption.encrypt(message).encode("utf-8") + b"\n"
        self._socket.sendall(frame)

    def _read_frame(self) -> Optional[bytes]:
        while b"\n" not in self._buffer:
            chunk = self._socket.recv(8192)
            if not chunk:
                if self._buffer:
                    frame = self._buffer
                    self._buffer = b""
                    return frame
                return None
            self._buffer += chunk

        frame, self._buffer = self._buffer.split(b"\n", 1)
        return frame.rstrip(b"\r")


def load_config():
    base_dir = Path(__file__).resolve().parent
    for candidate in [base_dir / "config.py", base_dir / "example.config.py"]:
        if candidate.exists():
            spec = importlib.util.spec_from_file_location("runtime_config", candidate)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("No client config found. Copy example.config.py to config.py and fill in the values.")


if __name__ == "__main__":
    config = load_config()
    client = D3vSkymanClient(
        config.HOST,
        config.PORT,
        config.PASSWORD,
        config.IV,
        config.KEY,
    )
    response = client.send_command("CLI echo 'hello from Python' && echo 'streaming works';")
    print(response["result"])
