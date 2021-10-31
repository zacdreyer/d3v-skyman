<?php


namespace d3vskyman;


class d3vskyman {

    private encryptionHandler $_encryption;
    private socketHandler $_socket;
    private string $password;

    public function __construct($socket_host, $socket_port, $socket_password, $encryption_iv, $encryption_key){
        $this->_socket      = new socketHandler($socket_host, $socket_port);
        $this->_encryption  = new encryptionHandler($encryption_iv, $encryption_key);
        $this->password     = $socket_password;
    }

    public function sendCommand($command): array {

        $result = $this->_socket->sendCommand($this->_encryption->encrypt('AUTH '.$this->password));
        if($result['status'] == 'success') {
            $result = $this->_socket->sendCommand($this->_encryption->encrypt($command));
            if ($result['status'] == 'success') {
                $result['message'] = $this->_encryption->decrypt($result['message']);
            }
        }
        return $result;
    }
}

# [START] Socket Handler Class #
class socketHandler {

    private string $host;
    private string $port;

    public function __construct($socket_host, $socket_port){
        $this->host         = $socket_host;
        $this->port         = $socket_port;
    }

    public function sendCommand($command): array {
        $socket = socket_create(AF_INET, SOCK_STREAM, 0);
        if($socket) {
            if(socket_connect($socket, $this->host, $this->port)) {

                if(socket_write($socket, $command, strlen($command))) {
                    $answer = array('status' => 'success',
                        'message' => socket_read($socket, 1024)
                    );
                } else {
                    $answer = array('status' => 'failed',
                        'message' => 'Could not send data to server.'
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