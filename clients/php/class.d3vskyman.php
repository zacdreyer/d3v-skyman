<?php

namespace d3vskyman;

class d3vskyman
{
    private encryptionHandler $_encryption;
    private socketHandler $_socket;

    public function __construct($socket_host, $socket_port, $socket_password, $encryption_iv, $encryption_key)
    {
        $this->_encryption = new encryptionHandler($encryption_iv, $encryption_key);
        $this->_socket = new socketHandler($socket_host, $socket_port, $socket_password, $this->_encryption);
    }

    public function sendCommand($command): array
    {
        return $this->_socket->sendCommand($command);
    }
}

class socketHandler
{
    private string $host;
    private string $port;
    private string $password;
    private int $buffer;
    private encryptionHandler $_encryption;
    private string $socketBuffer = '';

    public function __construct($socket_host, $socket_port, $socket_password, $encryptionHandler)
    {
        $this->host = $socket_host;
        $this->port = (int) $socket_port;
        $this->password = $socket_password;
        $this->_encryption = $encryptionHandler;
        $this->buffer = 26214400;
    }

    public function sendCommand($command): array
    {
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            return ['status' => 'failed', 'message' => 'Could not create socket.'];
        }

        if (!socket_connect($socket, $this->host, $this->port)) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'Could not connect to server.'];
        }

        $welcome = $this->readFrame($socket);
        if ($welcome === null) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'No server handshake received.'];
        }

        if (!$this->writeFrame($socket, 'AUTH ' . $this->password . ';')) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'Could not auth with server.'];
        }

        $authResult = $this->readFrame($socket);
        if ($authResult === null) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'No authentication response received.'];
        }

        $authPayload = $this->_encryption->decrypt($authResult);
        if (strpos($authPayload, 'Authentication failed') !== false) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'Authentication failed.'];
        }

        if (!$this->writeFrame($socket, $command)) {
            socket_close($socket);
            return ['status' => 'failed', 'message' => 'Could not send data to server.'];
        }

        $result = '';
        $stream = [];

        while (($frame = $this->readFrame($socket)) !== null) {
            $payload = $this->_encryption->decrypt($frame);
            if ($payload === 'STREAM_END') {
                break;
            }

            if (substr($payload, 0, strlen('STREAM_CHUNK:')) === 'STREAM_CHUNK:') {
                $chunk = substr($payload, strlen('STREAM_CHUNK:'));
                $result .= $chunk;
                $stream[] = $chunk;
                continue;
            }

            $result .= $payload;
        }

        socket_close($socket);

        return [
            'status' => 'success',
            'message' => 'Command successfully sent to server.',
            'result' => $result,
            'stream' => $stream,
            'enc_result' => $result,
        ];
    }

    private function readFrame($socket): ?string
    {
        while (true) {
            if (strpos($this->socketBuffer, "\n") !== false) {
                $parts = explode("\n", $this->socketBuffer, 2);
                $frame = $parts[0];
                $this->socketBuffer = $parts[1] ?? '';
                return rtrim($frame, "\r");
            }

            $chunk = @socket_read($socket, 8192);
            if ($chunk === false || $chunk === '') {
                if ($this->socketBuffer !== '') {
                    $frame = rtrim($this->socketBuffer, "\r");
                    $this->socketBuffer = '';
                    return $frame;
                }

                return null;
            }

            $this->socketBuffer .= $chunk;
        }
    }

    private function writeFrame($socket, $message): bool
    {
        $frame = $this->_encryption->encrypt($message) . "\n";
        return socket_write($socket, $frame, strlen($frame)) !== false;
    }
}

class encryptionHandler
{
    private $iv = '';
    private $key = '';
    private $block_size = 16;

    public function __construct($encryption_iv, $encryption_key)
    {
        $this->iv = $encryption_iv;
        $this->key = $encryption_key;
    }

    public function encrypt($data): string
    {
        $payload = $this->pad($data);
        return base64_encode(openssl_encrypt($payload, 'AES-256-CBC', $this->key, OPENSSL_RAW_DATA, $this->iv));
    }

    public function decrypt($data): string
    {
        $plain = openssl_decrypt(base64_decode($data), 'AES-256-CBC', $this->key, OPENSSL_RAW_DATA, $this->iv);
        return $this->unpad($plain);
    }

    private function pad($data): string
    {
        $data = (string) $data;
        $len = strlen($data);
        $padding = $this->block_size - ($len % $this->block_size);
        return $data . str_repeat(chr($padding), $padding);
    }

    private function unpad($data): string
    {
        if ($data === false) {
            return '';
        }

        $len = strlen($data);
        if ($len === 0) {
            return '';
        }

        $padding = ord($data[$len - 1]);
        if ($padding < 1 || $padding > $this->block_size) {
            return $data;
        }

        if (substr($data, $len - $padding) !== str_repeat(chr($padding), $padding)) {
            return $data;
        }

        return substr($data, 0, $len - $padding);
    }
}
