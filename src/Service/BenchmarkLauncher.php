<?php
namespace App\Service;

final class BenchmarkLauncher
{
    public function __construct(
        private readonly Database $database,
        private readonly string $projectDir = __DIR__.'/../..',
        private readonly string $pythonExecutable = 'H:\Python\pythoncore-3.14-64\python.exe',
        private readonly string $dependencyRoot = 'H:\temp\EZChords_Benchmark\deps',
        private readonly bool $keepUploads = true,
    ) {}

    public function launch(int $runId, string $audioPath, string $signature): void
    {
        $projectDir = realpath($this->projectDir) ?: $this->projectDir;
        $worker = $projectDir.DIRECTORY_SEPARATOR.'python'.DIRECTORY_SEPARATOR.'worker.py';

        if (!is_file($this->pythonExecutable)) {
            throw new \RuntimeException('Python introuvable: '.$this->pythonExecutable);
        }
        if (!is_file($worker)) {
            throw new \RuntimeException('Worker introuvable: '.$worker);
        }

        $args = [
            $this->pythonExecutable,
            $worker,
            '--db', $this->database->path(),
            '--run-id', (string)$runId,
            '--audio', $audioPath,
            '--signature', $signature,
            '--deps', $this->dependencyRoot,
            '--keep-upload', $this->keepUploads ? '1' : '0',
        ];

        $command = implode(' ', array_map([$this, 'quote'], $args));

        passthru($command, $exitCode);

        if ($exitCode !== 0) {
            $run = $this->database->run($runId);
            $error = $run['error'] ?? 'Analyse Python en erreur.';
            throw new \RuntimeException((string)$error);
        }
    }

    private function quote(string $arg): string
    {
        if (PHP_OS_FAMILY === 'Windows') {
            return '"'.str_replace('"', '\\"', $arg).'"';
        }

        return escapeshellarg($arg);
    }
}
