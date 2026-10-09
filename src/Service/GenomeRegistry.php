<?php
namespace App\Service;

final class GenomeRegistry
{
    public function __construct(private readonly Database $db) {}

    public function ensureSchema(): void
    {
        $this->db->pdo()->exec(<<<'SQL'
CREATE TABLE IF NOT EXISTS genome_gene_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_key TEXT NOT NULL,
    revision_number INTEGER NOT NULL,
    revision_ref TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL,
    composition_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(gene_key, revision_number),
    UNIQUE(gene_key, fingerprint)
);
CREATE INDEX IF NOT EXISTS idx_genome_gene_key
ON genome_gene_revisions(gene_key, revision_number);

CREATE TABLE IF NOT EXISTS genome_region_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT NOT NULL CHECK(region IN ('profile','stems','chords','lyrics')),
    revision_number INTEGER NOT NULL,
    revision_ref TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL,
    pipeline_revision TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK(status IN ('candidate','promoted','rejected','superseded')),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    UNIQUE(region, revision_number),
    UNIQUE(region, fingerprint)
);
CREATE INDEX IF NOT EXISTS idx_genome_region_revision
ON genome_region_revisions(region, revision_number);

CREATE TABLE IF NOT EXISTS genome_region_revision_genes (
    region_revision_id INTEGER NOT NULL,
    gene_revision_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY(region_revision_id, position),
    UNIQUE(region_revision_id, gene_revision_id),
    FOREIGN KEY(region_revision_id)
        REFERENCES genome_region_revisions(id) ON DELETE CASCADE,
    FOREIGN KEY(gene_revision_id)
        REFERENCES genome_gene_revisions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS genome_region_revision_parents (
    child_region_revision_id INTEGER NOT NULL,
    parent_region_revision_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'evolution',
    PRIMARY KEY(child_region_revision_id,parent_region_revision_id,role),
    FOREIGN KEY(child_region_revision_id)
        REFERENCES genome_region_revisions(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_region_revision_id)
        REFERENCES genome_region_revisions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS scientific_run_genome (
    run_id INTEGER PRIMARY KEY,
    region_revision_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES scientific_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(region_revision_id)
        REFERENCES genome_region_revisions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS genome_region_baselines (
    region TEXT PRIMARY KEY
        CHECK(region IN ('profile','stems','chords','lyrics')),
    region_revision_id INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(region_revision_id)
        REFERENCES genome_region_revisions(id) ON DELETE RESTRICT
);
SQL);
    }

    public function captureRunGenome(
        int $runId,
        string $region,
        array $manifest,
    ): array {
        $this->ensureSchema();

        if (!in_array($region, ['profile','stems','chords','lyrics'], true)) {
            throw new \InvalidArgumentException('genome_invalid_region');
        }

        $run = $this->scientificRun($runId);
        if ($run === null) {
            throw new \RuntimeException('genome_scientific_run_missing');
        }
        if ((string)$run['item'] !== $region) {
            throw new \RuntimeException('genome_run_region_mismatch');
        }

        $genes = $manifest['genes'] ?? null;
        if (!is_array($genes) || $genes === []) {
            throw new \RuntimeException('genome_manifest_genes_missing');
        }

        $pipelineRevision = trim((string)($manifest['pipeline_revision'] ?? ''));
        $pdo = $this->db->pdo();
        $pdo->exec('BEGIN IMMEDIATE');

        try {
            $existingLink = $pdo->prepare(
                'SELECT region_revision_id FROM scientific_run_genome WHERE run_id=?'
            );
            $existingLink->execute([$runId]);
            $linked = $existingLink->fetchColumn();

            $geneRows = [];
            $position = 0;
            foreach ($genes as $gene) {
                if (!is_array($gene)) {
                    throw new \RuntimeException('genome_gene_manifest_invalid');
                }
                $geneKey = trim((string)($gene['id'] ?? ''));
                if ($geneKey === '') {
                    throw new \RuntimeException('genome_gene_id_missing');
                }

                $composition = $this->canonicalize($gene);
                $fingerprint = hash('sha256', $this->canonicalJson($composition));

                $stmt = $pdo->prepare(
                    'SELECT * FROM genome_gene_revisions
                     WHERE gene_key=? AND fingerprint=?'
                );
                $stmt->execute([$geneKey, $fingerprint]);
                $geneRow = $stmt->fetch();

                if (!$geneRow) {
                    $next = $pdo->prepare(
                        'SELECT COALESCE(MAX(revision_number),0)+1
                         FROM genome_gene_revisions WHERE gene_key=?'
                    );
                    $next->execute([$geneKey]);
                    $revisionNumber = (int)$next->fetchColumn();
                    $revisionRef = $geneKey.'.r'.$revisionNumber;

                    $pdo->prepare(
                        'INSERT INTO genome_gene_revisions(
                            gene_key,revision_number,revision_ref,
                            fingerprint,composition_json,created_at
                         ) VALUES(?,?,?,?,?,?)'
                    )->execute([
                        $geneKey,
                        $revisionNumber,
                        $revisionRef,
                        $fingerprint,
                        $this->canonicalJson($composition),
                        gmdate('c'),
                    ]);

                    $stmt = $pdo->prepare(
                        'SELECT * FROM genome_gene_revisions WHERE id=?'
                    );
                    $stmt->execute([(int)$pdo->lastInsertId()]);
                    $geneRow = $stmt->fetch();
                }

                $geneRows[] = ['position' => $position++, 'row' => $geneRow];
            }

            $regionIdentity = [
                'schema' => 'ezstudio.genome.region.v1',
                'region' => $region,
                'pipeline_revision' => $pipelineRevision,
                'genes' => array_map(
                    static fn(array $entry): array => [
                        'position' => (int)$entry['position'],
                        'gene_key' => (string)$entry['row']['gene_key'],
                        'gene_revision' => (string)$entry['row']['revision_ref'],
                        'fingerprint' => (string)$entry['row']['fingerprint'],
                    ],
                    $geneRows
                ),
            ];
            $regionFingerprint = hash(
                'sha256',
                $this->canonicalJson($regionIdentity)
            );

            $stmt = $pdo->prepare(
                'SELECT * FROM genome_region_revisions
                 WHERE region=? AND fingerprint=?'
            );
            $stmt->execute([$region, $regionFingerprint]);
            $regionRow = $stmt->fetch();

            if (!$regionRow) {
                $next = $pdo->prepare(
                    'SELECT COALESCE(MAX(revision_number),0)+1
                     FROM genome_region_revisions WHERE region=?'
                );
                $next->execute([$region]);
                $revisionNumber = (int)$next->fetchColumn();
                $revisionRef = strtoupper($region).'.r'.$revisionNumber;

                $baselineStmt = $pdo->prepare(
                    'SELECT region_revision_id
                     FROM genome_region_baselines WHERE region=?'
                );
                $baselineStmt->execute([$region]);
                $parentId = $baselineStmt->fetchColumn();

                if ($parentId === false) {
                    $latest = $pdo->prepare(
                        'SELECT id FROM genome_region_revisions
                         WHERE region=? ORDER BY revision_number DESC LIMIT 1'
                    );
                    $latest->execute([$region]);
                    $parentId = $latest->fetchColumn();
                }

                $isFirst = $parentId === false;
                $status = $isFirst ? 'promoted' : 'candidate';

                $pdo->prepare(
                    'INSERT INTO genome_region_revisions(
                        region,revision_number,revision_ref,fingerprint,
                        pipeline_revision,status,metadata_json,created_at
                     ) VALUES(?,?,?,?,?,?,?,?)'
                )->execute([
                    $region,
                    $revisionNumber,
                    $revisionRef,
                    $regionFingerprint,
                    $pipelineRevision,
                    $status,
                    $this->canonicalJson([
                        'manifest_schema' => $manifest['schema']
                            ?? 'ezstudio.genome.region.v1',
                    ]),
                    gmdate('c'),
                ]);
                $regionId = (int)$pdo->lastInsertId();

                $linkGene = $pdo->prepare(
                    'INSERT INTO genome_region_revision_genes(
                        region_revision_id,gene_revision_id,position
                     ) VALUES(?,?,?)'
                );
                foreach ($geneRows as $entry) {
                    $linkGene->execute([
                        $regionId,
                        (int)$entry['row']['id'],
                        (int)$entry['position'],
                    ]);
                }

                if ($parentId !== false) {
                    $pdo->prepare(
                        'INSERT OR IGNORE INTO genome_region_revision_parents(
                            child_region_revision_id,parent_region_revision_id,role
                         ) VALUES(?,?,?)'
                    )->execute([$regionId, (int)$parentId, 'evolution']);
                }

                if ($isFirst) {
                    $pdo->prepare(
                        'INSERT INTO genome_region_baselines(
                            region,region_revision_id,updated_at
                         ) VALUES(?,?,?)'
                    )->execute([$region, $regionId, gmdate('c')]);
                }

                $stmt = $pdo->prepare(
                    'SELECT * FROM genome_region_revisions WHERE id=?'
                );
                $stmt->execute([$regionId]);
                $regionRow = $stmt->fetch();
            }

            if ($linked !== false && (int)$linked !== (int)$regionRow['id']) {
                throw new \RuntimeException('genome_run_link_is_immutable');
            }

            if ($linked === false) {
                $pdo->prepare(
                    'INSERT INTO scientific_run_genome(
                        run_id,region_revision_id,captured_at
                     ) VALUES(?,?,?)'
                )->execute([$runId, (int)$regionRow['id'], gmdate('c')]);
            }

            $pdo->commit();
            return $this->regionRevision((int)$regionRow['id']);
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;
        }
    }

    public function regionRevision(int $id): array
    {
        $this->ensureSchema();

        $stmt = $this->db->pdo()->prepare(
            'SELECT * FROM genome_region_revisions WHERE id=?'
        );
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        if (!$row) {
            throw new \RuntimeException('genome_region_revision_missing');
        }

        $genes = $this->db->pdo()->prepare(
            'SELECT rg.position,g.*
             FROM genome_region_revision_genes rg
             JOIN genome_gene_revisions g ON g.id=rg.gene_revision_id
             WHERE rg.region_revision_id=?
             ORDER BY rg.position'
        );
        $genes->execute([$id]);

        $parents = $this->db->pdo()->prepare(
            'SELECT p.role,r.*
             FROM genome_region_revision_parents p
             JOIN genome_region_revisions r
               ON r.id=p.parent_region_revision_id
             WHERE p.child_region_revision_id=?
             ORDER BY r.revision_number'
        );
        $parents->execute([$id]);

        $row['metadata'] = json_decode((string)$row['metadata_json'], true) ?: [];
        $row['genes'] = array_map(
            function(array $gene): array {
                $gene['composition'] = json_decode(
                    (string)$gene['composition_json'],
                    true
                ) ?: [];
                return $gene;
            },
            $genes->fetchAll()
        );
        $row['parents'] = $parents->fetchAll();
        return $row;
    }

    public function genomeForRun(int $runId): ?array
    {
        $this->ensureSchema();
        $stmt = $this->db->pdo()->prepare(
            'SELECT region_revision_id FROM scientific_run_genome WHERE run_id=?'
        );
        $stmt->execute([$runId]);
        $id = $stmt->fetchColumn();
        return $id === false ? null : $this->regionRevision((int)$id);
    }

    public function promoteRegionRevision(int $id): array
    {
        $this->ensureSchema();
        $revision = $this->regionRevision($id);
        $region = (string)$revision['region'];

        $pdo = $this->db->pdo();
        $pdo->exec('BEGIN IMMEDIATE');
        try {
            $pdo->prepare(
                "UPDATE genome_region_revisions
                 SET status='superseded'
                 WHERE region=? AND status='promoted' AND id<>?"
            )->execute([$region, $id]);
            $pdo->prepare(
                "UPDATE genome_region_revisions SET status='promoted' WHERE id=?"
            )->execute([$id]);
            $pdo->prepare(
                'INSERT INTO genome_region_baselines(
                    region,region_revision_id,updated_at
                 ) VALUES(?,?,?)
                 ON CONFLICT(region) DO UPDATE SET
                    region_revision_id=excluded.region_revision_id,
                    updated_at=excluded.updated_at'
            )->execute([$region, $id, gmdate('c')]);
            $pdo->commit();
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;
        }

        return $this->regionRevision($id);
    }

    public function rejectRegionRevision(int $id): void
    {
        $this->ensureSchema();
        $this->db->pdo()->prepare(
            "UPDATE genome_region_revisions
             SET status='rejected'
             WHERE id=? AND status!='promoted'"
        )->execute([$id]);
    }

    public function diffRegionRevisions(int $fromId, int $toId): array
    {
        $from = $this->regionRevision($fromId);
        $to = $this->regionRevision($toId);

        if ((string)$from['region'] !== (string)$to['region']) {
            throw new \InvalidArgumentException('genome_diff_region_mismatch');
        }

        $index = static function(array $revision): array {
            $out = [];
            foreach ($revision['genes'] as $gene) {
                $out[(string)$gene['gene_key']] = $gene;
            }
            return $out;
        };

        $a = $index($from);
        $b = $index($to);
        $added = [];
        $removed = [];
        $changed = [];
        $unchanged = [];

        foreach ($b as $key => $gene) {
            if (!isset($a[$key])) {
                $added[] = $gene['revision_ref'];
            } elseif (
                (string)$a[$key]['fingerprint']
                !== (string)$gene['fingerprint']
            ) {
                $changed[] = [
                    'gene' => $key,
                    'from' => $a[$key]['revision_ref'],
                    'to' => $gene['revision_ref'],
                ];
            } else {
                $unchanged[] = $gene['revision_ref'];
            }
        }

        foreach ($a as $key => $gene) {
            if (!isset($b[$key])) {
                $removed[] = $gene['revision_ref'];
            }
        }

        return [
            'region' => (string)$from['region'],
            'from' => (string)$from['revision_ref'],
            'to' => (string)$to['revision_ref'],
            'added' => $added,
            'removed' => $removed,
            'changed' => $changed,
            'unchanged' => $unchanged,
        ];
    }

    private function scientificRun(int $runId): ?array
    {
        $stmt = $this->db->pdo()->prepare(
            'SELECT * FROM scientific_runs WHERE id=?'
        );
        $stmt->execute([$runId]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    private function canonicalJson(array $value): string
    {
        return json_encode(
            $this->canonicalize($value),
            JSON_UNESCAPED_UNICODE
            | JSON_UNESCAPED_SLASHES
            | JSON_PRESERVE_ZERO_FRACTION
            | JSON_THROW_ON_ERROR
        );
    }

    private function canonicalize(mixed $value): mixed
    {
        if (!is_array($value)) {
            return $value;
        }
        if (array_is_list($value)) {
            return array_map(
                fn(mixed $item): mixed => $this->canonicalize($item),
                $value
            );
        }
        ksort($value, SORT_STRING);
        foreach ($value as $key => $item) {
            $value[$key] = $this->canonicalize($item);
        }
        return $value;
    }
}
