<?php

use d3vskyman\d3vskyman;

require_once 'class.d3vskyman.php';
require_once 'config.php';

global $_CONFIG;
$d3vskyman = new d3vskyman(
    $_CONFIG->SERVER->HOST,
    $_CONFIG->SERVER->PORT,
    $_CONFIG->SERVER->PASSWORD,
    $_CONFIG->ENCRYPTION->IV,
    $_CONFIG->ENCRYPTION->KEY
);

print_r($d3vskyman->sendCommand('CLI ls -la'));