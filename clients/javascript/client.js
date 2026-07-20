const net = require('net');
const crypto = require('crypto');
const config = require('./config');

class EncryptionHandler {
  constructor(key, iv) {
    this.key = Buffer.from(key, 'utf8');
    this.iv = Buffer.from(iv, 'utf8');
    this.blockSize = 16;
  }

  encrypt(data) {
    const padded = this.pad(Buffer.from(data, 'utf8'));
    const cipher = crypto.createCipheriv('aes-256-cbc', this.key, this.iv);
    return Buffer.concat([cipher.update(padded), cipher.final()]).toString('base64');
  }

  decrypt(data) {
    const decipher = crypto.createDecipheriv('aes-256-cbc', this.key, this.iv);
    const decrypted = Buffer.concat([decipher.update(Buffer.from(data, 'base64')), decipher.final()]);
    return this.unpad(decrypted).toString('utf8');
  }

  pad(data) {
    const padLength = this.blockSize - (data.length % this.blockSize);
    const padding = Buffer.alloc(padLength, padLength);
    return Buffer.concat([data, padding]);
  }

  unpad(data) {
    if (!data.length) return Buffer.alloc(0);
    const padLength = data[data.length - 1];
    if (padLength < 1 || padLength > this.blockSize) return data;
    return data.subarray(0, data.length - padLength);
  }
}

class D3vSkymanClient {
  constructor(host, port, password, iv, key) {
    this.host = host;
    this.port = port;
    this.password = password;
    this.encryption = new EncryptionHandler(key, iv);
    this.buffer = Buffer.alloc(0);
    this.socket = null;
    this.phase = 'welcome';
    this.result = '';
    this.streamChunks = [];
  }

  sendCommand(command) {
    return new Promise((resolve, reject) => {
      const socket = net.createConnection(this.port, this.host);
      this.socket = socket;

      socket.on('connect', () => {
        socket.on('data', (chunk) => {
          this.buffer = Buffer.concat([this.buffer, chunk]);
          let newlineIndex;
          while ((newlineIndex = this.buffer.indexOf(Buffer.from('\n'))) !== -1) {
            const frame = this.buffer.subarray(0, newlineIndex).toString('utf8').replace(/\r$/, '');
            this.buffer = this.buffer.subarray(newlineIndex + 1);

            if (this.phase === 'welcome') {
              this.phase = 'auth';
              this.writeFrame(`AUTH ${this.password};`);
              continue;
            }

            if (this.phase === 'auth') {
              this.phase = 'command';
              this.writeFrame(command);
              continue;
            }

            const payload = this.encryption.decrypt(frame);
            if (payload === 'STREAM_END') {
              resolve({ status: 'success', result: this.result, stream: this.streamChunks });
              socket.end();
              return;
            }

            if (payload.startsWith('STREAM_CHUNK:')) {
              const chunkText = payload.slice('STREAM_CHUNK:'.length);
              this.result += chunkText;
              this.streamChunks.push(chunkText);
            } else {
              this.result += payload;
              this.streamChunks.push(payload);
            }
          }
        });
      });

      socket.on('error', reject);
    });
  }

  writeFrame(message) {
    const payload = this.encryption.encrypt(message) + '\n';
    this.socket.write(payload);
  }
}

const client = new D3vSkymanClient(config.host, config.port, config.password, config.iv, config.key);
client.result = '';
client.streamChunks = [];
client.sendCommand("CLI echo 'hello from JavaScript' && echo 'streaming works';")
  .then((response) => {
    console.log(response.result);
  })
  .catch((error) => {
    console.error(error);
  });
