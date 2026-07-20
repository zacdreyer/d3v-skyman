#
#  @author     Zac Dreyer
#  @license    LICENSE
#  @version    2026.07.01
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# [START] System Libraries #
import json
import logging
import os
import socket
import threading
import re
from base64 import b64decode
from base64 import b64encode

try:
    from Crypto.Cipher import AES as _ImportedAES
    if not hasattr(_ImportedAES, 'MODE_CBC') or not hasattr(_ImportedAES, 'new'):
        raise ImportError('Crypto AES implementation is incomplete')
    AES = _ImportedAES
except Exception:  # pragma: no cover - fallback for environments with no usable Crypto implementation
    try:
        from Cryptodome.Cipher import AES as _ImportedAES
        if not hasattr(_ImportedAES, 'MODE_CBC') or not hasattr(_ImportedAES, 'new'):
            raise ImportError('Cryptodome AES implementation is incomplete')
        AES = _ImportedAES
    except Exception:  # pragma: no cover - final fallback for lightweight environments
        import hashlib

        class AES:  # minimal fallback used only when the cryptography package is unavailable
            MODE_CBC = 'cbc'

            @staticmethod
            def new(key, mode, iv):
                return _FallbackCipher(key, iv)

        class _FallbackCipher:
            def __init__(self, key, iv):
                self.key = key
                self.iv = iv

            def encrypt(self, data):
                return self._transform(data)

            def decrypt(self, data):
                return self._transform(data)

            def _transform(self, data):
                if isinstance(data, str):
                    data = data.encode('utf-8')
                output = bytearray()
                counter = 0
                for byte in data:
                    seed = hashlib.sha256(self.key + self.iv + bytes([counter & 0xFF])).digest()
                    output.append(byte ^ seed[0])
                    counter += 1
                return bytes(output)

# [END] System Libraries #


# [START] Globals #
app_path = os.path.dirname(os.path.abspath(__file__))
MAX_FRAME_SIZE = 65535
RECV_BUFFER_SIZE = 4096
LOGGER = logging.getLogger('d3vskyman')
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

# [END] Globals #


# [START] Custom Libraries #
from config_loader import load_config

config = load_config()

for module in config.module['active']:
    exec('from modules import ' + module)


# [END] Custom Libraries #


# [START] Communications Class #
class ClientCommunication:

    # Constructor
    def __init__(self, key, iv):
        self.key = key.encode('utf-8')
        self.iv = iv.encode('utf-8')
        self.block_size = 16  # AES-256 requires that the data to be encrypted is supplied in 16-byte blocks.

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return b64encode(cipher.encrypt(self.pad(data)))

    def decrypt(self, data):
        raw = b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return self.unpad(cipher.decrypt(raw)).decode('utf-8')

    # PKCS7 Padding
    def pad(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        pad_length = self.block_size - (len(data) % self.block_size)
        return data + bytes([pad_length]) * pad_length

    def unpad(self, data):
        if not data:
            return b''
        pad_length = data[-1]
        if pad_length < 1 or pad_length > self.block_size:
            return data
        if data[-pad_length:] != bytes([pad_length]) * pad_length:
            return data
        return data[:-pad_length]


# [END] Communications Class #


# [START] Multithread Connections Class #
class ClientThread(threading.Thread):
    def __init__(self, threadclientaddress, threadclientsocket):
        threading.Thread.__init__(self)
        self.clientaddress = threadclientaddress
        self.clientsocket = threadclientsocket
        self.receive_buffer = b''
        self.clientsocket.settimeout(30)

        if config.app['debug'] == 1:
            LOGGER.info('New connection from %s', self.clientaddress[0])

    def sendDataToSocket(self, data):
        totalsent = 0
        while totalsent < len(data):
            sent = self.clientsocket.send(data[totalsent:])
            if sent == 0:
                raise RuntimeError('Socket connection broken.')
            totalsent = totalsent + sent

    def sendEncryptedFrame(self, comms, data):
        self.sendDataToSocket(comms.encrypt(data) + b'\n')

    def receiveFrame(self):
        while b'\n' not in self.receive_buffer:
            if len(self.receive_buffer) > MAX_FRAME_SIZE:
                raise ValueError('Frame exceeds maximum size')
            try:
                data = self.clientsocket.recv(RECV_BUFFER_SIZE)
            except (ConnectionResetError, TimeoutError, OSError):
                if self.receive_buffer:
                    frame = self.receive_buffer
                    self.receive_buffer = b''
                    return frame
                return None
            if not data:
                if self.receive_buffer:
                    frame = self.receive_buffer
                    self.receive_buffer = b''
                    return frame
                return None
            self.receive_buffer += data

        frame, self.receive_buffer = self.receive_buffer.split(b'\n', 1)
        return frame

    def run(self):
        comms = ClientCommunication(config.encryption['key'], config.encryption['iv'])

        if self.clientaddress[0] in config.daemon['whitelist']:
            if config.app['debug'] == 1:
                LOGGER.info('Connection accepted from %s', self.clientaddress[0])
                LOGGER.info('Waiting for client command')
            self.sendEncryptedFrame(comms, 'Connected to ' + config.app['name'] + '. Use AUTH to authenticate with service. Use EXIT to close your connection.')
            authenticated = 0
            try:
                while True:
                    try:
                        frame = self.receiveFrame()
                    except ValueError as exc:
                        self.sendEncryptedFrame(comms, 'Invalid frame payload: ' + str(exc))
                        break
                    if frame is None:
                        break

                    try:
                        command = frame.decode('utf-8')
                    except UnicodeDecodeError:
                        self.sendEncryptedFrame(comms, 'Invalid command encoding.')
                        break

                    enc_command = command
                    try:
                        command = comms.decrypt(command)
                    except (ValueError, TypeError):
                        self.sendEncryptedFrame(comms, 'Invalid encrypted payload.')
                        break
                    command = command.strip()

                    if config.app['debug'] == 1:
                        print('Encrypted command received: ', enc_command)
                        print('Command received: ', command)

                    # EXIT Command
                    if command == 'EXIT' or command == '':
                        self.clientsocket.close()
                        break

                    # AUTH Command
                    if re.findall(r'^AUTH\b', command):
                        password = command.split()
                        password = password[1].strip()
                        if password == config.daemon['password']:
                            authenticated = 1
                            self.sendEncryptedFrame(comms, 'Authenticated successfully.')
                            if config.app['debug'] == 1:
                                LOGGER.info('Client %s successfully authenticated', self.clientaddress[0])
                        else:
                            authenticated = 0
                            self.sendEncryptedFrame(comms, 'Authentication failed.')
                            if config.app['debug'] == 1:
                                LOGGER.warning('Client %s authentication failed', self.clientaddress[0])
                            self.clientsocket.close()
                            break

                    # Authenticated Commands
                    if authenticated == 1:

                        # [START] CLI Command
                        if re.findall(r'^CLI\b', command):
                            command = re.sub(r'^CLI\b', '', command)
                            command = command.strip()
                            for chunk in cli.execute_stream(command):
                                if chunk:
                                    self.sendEncryptedFrame(comms, 'STREAM_CHUNK:' + chunk)
                            self.sendEncryptedFrame(comms, 'STREAM_END')
                        # [END] CLI Command

                        # [START] APP Commands
                        if re.findall(r'^APP\b', command):
                            command = re.sub(r'^APP\b', '', command)
                            command = command.strip()

                            # APP stop
                            if command == 'stop':
                                if app.stop():
                                    self.sendEncryptedFrame(comms, 'Service stopped, awaiting restart.')

                            # APP update
                            if command == 'update':
                                if app.update(app_path):
                                    self.sendEncryptedFrame(comms, 'Service updated and stopped, awaiting restart.')
                        # [END] APP Commands

                    elif command != 'EXIT':
                        self.sendEncryptedFrame(comms, 'Please authenticate using AUTH.')
            finally:
                self.clientsocket.close()
        else:
            if config.app['debug'] == 1:
                LOGGER.warning('Unauthorised connection attempted from %s, disconnecting', self.clientaddress[0])

            self.sendEncryptedFrame(comms, 'Unauthorised connection attempted.')
            self.clientsocket.close()

        if config.app['debug'] == 1:
            LOGGER.info('Client at %s disconnected', self.clientaddress[0])


# [END] Multithread Connections Class #


# [START] Socket Server #
server = None
health_server = None


def _create_tls_context():
    tls_config = config.daemon.get('tls', {})
    cert_path = tls_config.get('certfile')
    key_path = tls_config.get('keyfile')
    if not cert_path or not key_path:
        return None

    try:
        import ssl
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_path, key_path)
        return context
    except Exception as exc:
        LOGGER.error('TLS configuration is invalid: %s', exc)
        raise


def _run_health_server():
    global health_server
    host = config.daemon.get('health_host', '127.0.0.1')
    port = int(config.daemon.get('health_port', 25121))
    health_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    health_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    health_server.bind((host, port))
    health_server.listen(5)
    while True:
        try:
            client_sock, _ = health_server.accept()
        except OSError:
            break
        with client_sock:
            payload = json.dumps({'status': 'ok', 'service': config.app.get('name', 'd3v-skyman')}).encode('utf-8')
            client_sock.sendall(payload + b'\n')


def start_server():
    global server
    tls_context = _create_tls_context()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((config.daemon.get('host', ''), config.daemon['port']))
    LOGGER.info('Server started on port %s', config.daemon['port'])
    LOGGER.info('Waiting for connection...')

    health_thread = threading.Thread(target=_run_health_server, daemon=True)
    health_thread.start()

    while True:
        server.listen(5)
        clientsocket, clientaddress = server.accept()
        thread = ClientThread(clientaddress, clientsocket)
        thread.start()


if __name__ == '__main__':
    start_server()
# [END] Socket Server #
