<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$dirs=[$root.'/templates',$root.'/src'];
$legacy=[];
$canonical=0;

foreach($dirs as $dir){
    if(!is_dir($dir)) continue;
    $it=new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir,FilesystemIterator::SKIP_DOTS)
    );
    foreach($it as $file){
        if(!$file->isFile()) continue;
        $text=file_get_contents($file->getPathname());
        if($text===false) continue;
        if(str_contains($text,'ZIP ADN')) $legacy[]=$file->getPathname();
        if(str_contains($text,'Exporter les Presets')) $canonical++;
    }
}

if($legacy!==[]){
    throw new RuntimeException("legacy_export_label_remains:\n".implode("\n",$legacy));
}
if($canonical<1){
    throw new RuntimeException('canonical_export_label_missing');
}

echo "TERMINOLOGY_EXPORT_LABEL_HOTFIX_CONTRACT_OK\n";
echo "Visible export label is canonical\n";
