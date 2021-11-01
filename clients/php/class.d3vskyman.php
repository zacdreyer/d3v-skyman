<?php


namespace d3vskyman;


class d3vskyman {

    private encryptionHandler $_encryption;
    private socketHandler $_socket;

    public function __construct($socket_host, $socket_port, $socket_password, $encryption_iv, $encryption_key){
        $this->_encryption  = new encryptionHandler($encryption_iv, $encryption_key);
        $this->_socket      = new socketHandler($socket_host, $socket_port, $socket_password, $this->_encryption);
    }

    public function sendCommand($command): array {

        return $this->_socket->sendCommand($command);

    }
}

# [START] Socket Handler Class #
class socketHandler {

    private string $host;
    private string $port;
    private string $password;
    private int $buffer;
    private encryptionHandler $_encryption;

    public function __construct($socket_host, $socket_port, $socket_password, &$encryptionHandler){
        $this->host         = $socket_host;
        $this->port         = $socket_port;
        $this->password     = $socket_password;
        $this->_encryption  = $encryptionHandler;
        $this->buffer       = 26214400;
    }

    public function sendCommand($command): array {
        $socket = socket_create(AF_INET, SOCK_STREAM, 0);
        if($socket) {
            if(socket_connect($socket, $this->host, $this->port)) {

                $auth_command = $this->_encryption->encrypt('AUTH '.$this->password.';');
                if(socket_write($socket, $auth_command, strlen($auth_command))) {

                    sleep(1); // Delay to allow for auth first
                    $command = $this->_encryption->encrypt($command);
                    if (socket_write($socket, $command, strlen($command))) {

                        $enc_payload = socket_read($socket, $this->buffer);
                        $payload = $this->_encryption->decrypt($enc_payload);

                        if(empty(trim($payload))) { $payload = 'No result or result to large to decode.'; }

                        $answer = array('status' => 'success',
                            'message' => 'Command successfully sent to server.',
                            'result' => $payload,
                            'enc_result' => $enc_payload
                        );

                    } else {
                        $answer = array('status' => 'failed',
                            'message' => 'Could not send data to server.'
                        );
                    }

                } else {
                    $answer = array('status' => 'failed',
                        'message' => 'Could not auth with server.'
                    );
                }

            } else {
                $answer = array('status' => 'failed',
                    'message' => 'Could not connect to server.'
                );
            }

            socket_close($socket);
        } else {
            $answer = array('status' => 'failed',
                'message' => 'Could not create socket.'
            );
        }

        return $answer;
    }
}
# [END] Socket Handler Class #


# [START] Encryption Handler Class #
class encryptionHandler {

    private $iv = '';
    private $key = '';
    private $block_size = 16;

    public function __construct($encryption_iv, $encryption_key){
        $this->iv           = $encryption_iv;
        $this->key          = $encryption_key;
    }

    public function encrypt($data): string
    {
        return base64_encode(openssl_encrypt($this->pad($data), 'AES-256-CBC', $this->key,  OPENSSL_RAW_DATA, $this->iv));
    }

    public function decrypt($data): string
    {
        return $this->unpad(openssl_decrypt(base64_decode($data), 'AES-256-CBC', $this->key,  OPENSSL_RAW_DATA, $this->iv));
    }

    private function pad($data): string
    {
        $padding = ($this->block_size - (strlen($data) % $this->block_size)) * ($this->block_size - (strlen($data) % $this->block_size));
        return str_repeat(chr($padding), $this->block_size) . $data;
    }
    private function unpad($data): string
    {
        $len  = strlen($data) - $this->block_size;
        return substr($data, $this->block_size, $len);
    }
}
# [END] Encryption Handler Class #