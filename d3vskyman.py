#
#  @author     Zac Dreyer [D3V.Digital]
#  @license    LICENSE
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# [START] System Libraries #
import os
import socket
import threading
import re
from base64 import b64decode
from base64 import b64encode
from Crypto.Cipher import AES

# [END] System Libraries #


# [START] Globals #
app_path = os.path.dirname(os.path.abspath(__file__))

# [END] Globals #


# [START] Custom Libraries #
import config

for module in config.module['active']:
    exec("from modules import " + module)


# [END] Custom Libraries #


# [START] Communications Class #
class ClientCommunication:

    # Constructor
    def __init__(self, key, iv):
        self.key = key.encode('utf-8')
        self.iv = iv.encode('utf-8')
        self.block_size = 16  # AES-256 requires that the data to be encrypted is supplied in 16-byte blocks.

    def encrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return b64encode(self.iv + cipher.encrypt(self.pad(data).encode('utf-8')))

    def decrypt(self, data):
        raw = b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return self.unpad(cipher.decrypt(raw)).decode('utf-8')

    # PKCS7 Padding
    def pad(self, data):
        return data + chr(self.block_size - len(data) % self.block_size) * (
                    self.block_size - len(data) % self.block_size)

    def unpad(self, data):
        strlen = len(data) - self.block_size
        return data[self.block_size:strlen:1]

# [END] Communications Class #


# [START] Multithread Connections Class #
class ClientThread(threading.Thread):
    def __init__(self, threadclientaddress, threadclientsocket):
        threading.Thread.__init__(self)
        self.clientaddress = threadclientaddress
        self.clientsocket = threadclientsocket

        if config.app['debug'] == 1:
            print("New connection: ", self.clientaddress[0])

    def run(self):
        comms = ClientCommunication(config.encryption['key'], config.encryption['iv'])

        if self.clientaddress[0] in config.daemon['whitelist']:
            if config.app['debug'] == 1:
                print("Connection accepted from: ", self.clientaddress[0])
                print("Waiting for client command...")
            self.clientsocket.send(comms.encrypt(
                'Connected to ' + config.app['name'] + '. Use AUTH to authenticate with service. Use EXIT to close your'
                                                       ' connection.\r\n'))
            authenticated = 0
            try:
                while True:
                    data = self.clientsocket.recv(2048)
                    command = data.decode('utf8')
                    enc_command = command
                    command = comms.decrypt(command)
                    command = command.strip()

                    if config.app['debug'] == 1:
                        print("Encrypted command received: ", enc_command)
                        print("Command received: ", command)

                    # EXIT Command
                    if command == 'EXIT' or command == '':
                        self.clientsocket.close()
                        break

                    # AUTH Command
                    if re.findall(r"^AUTH\b", command):
                        password = command.split()
                        password = password[1].strip()
                        if password == config.daemon['password']:
                            authenticated = 1
                            self.clientsocket.send(comms.encrypt('Authenticated successfully. \r\n'))
                            if config.app['debug'] == 1:
                                print("Client ", self.clientaddress[0], " successfully authenticated.")
                        else:
                            authenticated = 0
                            self.clientsocket.send(comms.encrypt('Authentication failed. \r\n'))
                            if config.app['debug'] == 1:
                                print("Client ", self.clientaddress[0], " authentication failed.")
                            self.clientsocket.close()
                            break

                    # Authenticated Commands
                    if authenticated == 1:

                        # [START] CLI Command
                        if re.findall(r"^CLI\b", command):
                            command = re.sub(r"^CLI\b", "", command)
                            command = command.strip()
                            self.clientsocket.send(comms.encrypt(cli.execute(command)))
                        # [END] CLI Command

                        # [START] APP Commands
                        if re.findall(r"^APP\b", command):
                            command = re.sub(r"^APP\b", "", command)
                            command = command.strip()

                            # APP stop
                            if command == 'stop':
                                if app.stop():
                                    self.clientsocket.send(comms.encrypt("Service stopped, awaiting restart."))

                            # APP update
                            if command == 'update':
                                if app.update(app_path):
                                    self.clientsocket.send(comms.encrypt("Service updated and stopped, awaiting "
                                                                         "restart."))
                        # [END] APP Commands

                    elif command != 'EXIT':
                        self.clientsocket.send(comms.encrypt('Please authenticate using AUTH. \r\n'))
            finally:
                self.clientsocket.close()
        else:
            if config.app['debug'] == 1:
                print("Unauthorised connection attempted from ", self.clientaddress[0], ", disconnecting...")

            self.clientsocket.send(comms.encrypt('Unauthorised connection attempted.'))
            self.clientsocket.close()

        if config.app['debug'] == 1:
            print("Client at ", self.clientaddress[0], " disconnected...")


# [END] Multithread Connections Class #


# [START] Socket Server #
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', config.daemon['port']))
if config.app['debug'] == 1:
    print("Server started on port " + str(config.daemon['port']))
    print("Waiting for connection...")
while True:
    server.listen(1)
    clientsocket, clientaddress = server.accept()
    thread = ClientThread(clientaddress, clientsocket)
    thread.start()
# [END] Socket Server #
