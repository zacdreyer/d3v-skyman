<?php

$_CONFIG = new stdClass();


# Debug Setting
$_CONFIG->DEBUG                 = 1;


# Server Config
$_CONFIG->SERVER = new stdClass();
$_CONFIG->SERVER->HOST          = '';
$_CONFIG->SERVER->PORT          = '';
$_CONFIG->SERVER->PASSWORD      = '';


# Encryption Config - Generate with https://www.allkeysgenerator.com/Random/Security-Encryption-Key-Generator.aspx
$_CONFIG->ENCRYPTION = new stdClass();
$_CONFIG->ENCRYPTION->IV        = ''; # Should be 16 characters (16 bytes / 128 bit)
$_CONFIG->ENCRYPTION->KEY       = ''; # Should be 32 characters (32 bytes / 256 bit)
