<?php

declare(strict_types=1);

namespace App\Controller;

use App\Service\Database;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\BinaryFileResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class ProfileFeedbackController extends AbstractController
{
    #[Route(
        '/catalogue/{id<\d+>}/profile-feedback.zip',
        name: 'profile_feedback_zip',
        methods: ['GET']
    )]
    public function download(int $id, Database $db): Response
    {
        $song = $db->song($id);
        if ($song === null) {
            return new Response('catalog_song_not_found', 404);
        }

        $projectRoot = dirname(__DIR__, 2);
        $python = (string)(
            getenv('EZSTUDIO_ANALYSIS_PYTHON')
            ?: 'H:\\Python\\pythoncore-3.14-64\\python.exe'
        );
        $script = $projectRoot
            .DIRECTORY_SEPARATOR.'scripts'
            .DIRECTORY_SEPARATOR.'export-profile-adn.py';

        if (!is_file($python) || !is_file($script)) {
            return new Response('profile_feedback_runtime_missing', 500);
        }

        $runtimeRoot = rtrim(
            (string)(getenv('EZSTUDIO_RUNTIME_ROOT') ?: 'H:\\temp\\EZStudio_lab'),
            '\\/'
        );
        $exportDir = $runtimeRoot
            .DIRECTORY_SEPARATOR.'exports'
            .DIRECTORY_SEPARATOR.'profile-feedback';
        if (!is_dir($exportDir)) {
            mkdir($exportDir, 0777, true);
        }

        $safe = preg_replace(
            '/[^A-Za-z0-9._-]+/',
            '-',
            trim((string)$song['title'].' '.(string)$song['artist'])
        ) ?: 'song-'.$id;

        $output = $exportDir
            .DIRECTORY_SEPARATOR.'EZStudio_PROFILE_ADN_'
            .trim($safe, '-._')
            .'_'.gmdate('Ymd_His').'.zip';

        $command = [
            $python,
            $script,
            '--db',
            $db->path(),
            '--song-id',
            (string)$id,
            '--output',
            $output,
        ];

        $descriptors = [
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w'],
        ];
        $pipes = [];
        $process = proc_open(
            $command,
            $descriptors,
            $pipes,
            $projectRoot,
            null,
            ['bypass_shell' => true]
        );

        if (!is_resource($process)) {
            return new Response('profile_feedback_process_start_failed', 500);
        }

        $stdout = stream_get_contents($pipes[1]) ?: '';
        $stderr = stream_get_contents($pipes[2]) ?: '';
        fclose($pipes[1]);
        fclose($pipes[2]);
        $rc = proc_close($process);

        if ($rc !== 0 || !is_file($output)) {
            return new Response(
                "profile_feedback_export_failed\n"
                ."returncode=".$rc."\n"
                .$stdout."\n".$stderr,
                500,
                ['Content-Type' => 'text/plain; charset=UTF-8']
            );
        }

        $response = new BinaryFileResponse($output);
        $response->headers->set('Content-Type', 'application/zip');
        $response->setContentDisposition('attachment', basename($output));
        $response->deleteFileAfterSend(true);

        return $response;
    }
}

