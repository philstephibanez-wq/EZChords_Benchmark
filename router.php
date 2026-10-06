<?php
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$file = __DIR__.'/public'.$path;

if ($path !== '/' && is_file($file)) {
    return false;
}

/*
 * Symfony Runtime determines the application bootstrap script from
 * SCRIPT_FILENAME. With the PHP built-in server, the router itself is the
 * script filename unless we point Runtime to public/index.php explicitly.
 */
$_SERVER['SCRIPT_FILENAME'] = __DIR__.'/public/index.php';
$_SERVER['SCRIPT_NAME'] = '/index.php';

require __DIR__.'/public/index.php';
