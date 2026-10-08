from pathlib import Path
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "migrate_r3a2",
    ROOT / "scripts" / "migrate-workbench-r3a2.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

db_variants = [
"""<?php
final class Database
{
    public function allRuns(): array
    {
        return [];
    }
}
""",
"<?php\r\nfinal class Database\r\n{\r\npublic function allRuns(): array { return []; }\r\n}\r\n",
]
for src in db_variants:
    out = mod.patch_database_text(src)
    assert "public function allSongs(): array" in out
    assert "public function runsForSong(int $songId): array" in out
    again = mod.patch_database_text(out)
    assert again == out

controller_variants = [
"""<?php
namespace App\\Controller;
use Symfony\\Component\\HttpFoundation\\BinaryFileResponse;
use Symfony\\Component\\HttpFoundation\\Response;
use Symfony\\Component\\Routing\\Attribute\\Route;
final class LabController
{
    #[Route('/', name: 'lab_index', methods: ['GET'])]
    public function index(Database $db): Response
    {
        return new Response('old');
    }

    #[Route('/lab/run/{id<\\d+>}', name: 'lab_run', methods: ['GET'])]
    public function run(int $id, Database $db): Response
    {
        return new Response('run');
    }
}
""",
"""<?php\r
namespace App\\Controller;\r
use Symfony\\Component\\HttpFoundation\\BinaryFileResponse;\r
use Symfony\\Component\\HttpFoundation\\Response;\r
use Symfony\\Component\\Routing\\Attribute\\Route;\r
final class LabController\r
{\r
#[Route('/', name: 'lab_index', methods: ['GET'])]\r
public function index(Database $db): Response { return new Response('old'); }\r
#[Route('/lab/run/{id<\\d+>}', name: 'lab_run', methods: ['GET'])]\r
public function run(int $id, Database $db): Response { return new Response('run'); }\r
}\r
""",
]
for src in controller_variants:
    out = mod.patch_controller_text(src)
    assert "use Symfony\\Component\\HttpFoundation\\Request;" in out
    assert "public function index(Request $request, Database $db): Response" in out
    assert "#[Route('/lab/run/" in out
    again = mod.patch_controller_text(out)
    assert again == out

print("EZSTUDIO_WORKBENCH_R3A2_SYNTHETIC_MIGRATION_OK")
