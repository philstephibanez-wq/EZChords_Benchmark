<?php

namespace App\Service;

final class ProfileFrenchSummary
{
    public function build(array $run): ?array
    {
        if (($run['state'] ?? null) !== 'done') return null;
        $metrics = is_array($run['metrics'] ?? null) ? $run['metrics'] : [];
        $diagnostics = is_array($run['diagnostics'] ?? null) ? $run['diagnostics'] : [];
        $tagging = is_array($diagnostics['tagging'] ?? null) ? $diagnostics['tagging'] : [];
        $view = is_array($diagnostics['profile_view'] ?? null) ? $diagnostics['profile_view'] : [];

        $tempo = isset($metrics['tempo']['bpm']) && is_numeric($metrics['tempo']['bpm']) ? (float)$metrics['tempo']['bpm'] : null;
        $meter = $metrics['time_signature']['label'] ?? $metrics['time_signature']['suggested_label'] ?? null;
        $meterConfidence = isset($metrics['time_signature']['confidence']) && is_numeric($metrics['time_signature']['confidence']) ? (float)$metrics['time_signature']['confidence'] : null;
        $key = $metrics['key']['label'] ?? ($view['tonal']['label'] ?? null);
        $key = is_string($key) && $key !== '' ? $this->translateKey($key) : null;

        $genres = $this->topLabels($tagging['genre'] ?? [], 4, 0.05, 'genre');
        $moods = $this->topLabels($tagging['mood'] ?? [], 4, 0.04, 'mood');
        $instruments = $this->topLabels($tagging['instrumentation'] ?? [], 5, 0.04, 'instrument');
        $voice = $this->topLabels($tagging['voice'] ?? [], 4, 0.04, 'voice');

        $accepted=[]; $contextual=[];
        foreach (($view['audioset']['agreements'] ?? []) as $row) {
            if (!is_array($row)) continue;
            $label=trim((string)($row['label'] ?? '')); if($label==='') continue;
            $decision=(string)($row['decision'] ?? '');
            if($decision==='accepted') $accepted[]=$this->translateLabel($label,'audioset');
            elseif($decision==='contextual') $contextual[]=$this->translateLabel($label,'audioset');
        }

        $sentences=[];
        if($tempo!==null) $sentences[]=sprintf('Le tempo mesuré est d’environ %d BPM (%s).',(int)round($tempo),$this->tempoQualifier($tempo));
        if(is_string($meter)&&$meter!=='') {
            $suffix=$meterConfidence!==null ? sprintf(' ; confiance opérationnelle %.0f %%',$meterConfidence*100) : '';
            $sentences[]=sprintf('La signature rythmique proposée est %s%s.',$meter,$suffix);
        }
        if($key!==null) $sentences[]=sprintf('La tonalité retenue par le consensus disponible est %s.',$key);
        if($genres!==[]) $sentences[]='Les tags de genre CLAP suggèrent surtout : '.$this->joinLabels($genres).'.';
        if($moods!==[]) $sentences[]='L’ambiance ressort principalement comme '.$this->joinLabels($moods).'.';
        if($instruments!==[]) $sentences[]='L’instrumentation probable met notamment en avant '.$this->joinLabels($instruments).'.';
        if($accepted!==[]) $sentences[]='La convergence AudioSet retient '.implode(', ',array_unique($accepted)).'.';
        if($voice!==[]) $sentences[]='Les observations vocales CLAP suggèrent '.$this->joinLabels($voice).'.';

        return [
            'text'=>implode(' ',$sentences), 'tempo_bpm'=>$tempo,
            'tempo_qualifier'=>$tempo!==null?$this->tempoQualifier($tempo):null,
            'meter'=>$meter, 'key'=>$key, 'genres'=>$genres, 'moods'=>$moods,
            'instrumentation'=>$instruments, 'voice'=>$voice,
            'audioset_accepted'=>array_values(array_unique($accepted)),
            'audioset_contextual'=>array_values(array_unique($contextual)),
            'notice'=>'Résumé déterministe dérivé de l’ADN. Les scores CLAP sont relatifs à la taxonomie comparée ; la confidence AudioSet n’est pas une probabilité calibrée.',
        ];
    }

    private function topLabels(mixed $rows,int $limit,float $minimum,string $family): array
    {
        if(!is_array($rows)) return [];
        $result=[];
        foreach($rows as $row){
            if(!is_array($row)) continue;
            $label=trim((string)($row['label']??''));
            $score=isset($row['score'])&&is_numeric($row['score'])?(float)$row['score']:null;
            if($label===''||$score===null||$score<$minimum) continue;
            $result[]=['label'=>$this->translateLabel($label,$family),'source_label'=>$label,'score'=>$score];
            if(count($result)>=$limit) break;
        }
        return $result;
    }

    private function joinLabels(array $rows): string
    {
        $labels=array_values(array_filter(array_map(static fn(array $r): string=>(string)($r['label']??''),$rows)));
        if(count($labels)<=1) return $labels[0]??'';
        $last=array_pop($labels); return implode(', ',$labels).' et '.$last;
    }

    private function tempoQualifier(float $bpm): string
    {
        return match(true){$bpm<70.0=>'lent',$bpm<100.0=>'modéré',$bpm<130.0=>'allant',default=>'rapide'};
    }

    private function translateKey(string $label): string
    {
        if(!preg_match('/^([A-G])([#b]?)[ ]+(major|minor)$/i',trim($label),$m)) return $label;
        $notes=['C'=>'Do','C#'=>'Do♯','Db'=>'Ré♭','D'=>'Ré','D#'=>'Ré♯','Eb'=>'Mi♭','E'=>'Mi','F'=>'Fa','F#'=>'Fa♯','Gb'=>'Sol♭','G'=>'Sol','G#'=>'Sol♯','Ab'=>'La♭','A'=>'La','A#'=>'La♯','Bb'=>'Si♭','B'=>'Si'];
        $note=strtoupper($m[1]).$m[2]; $mode=strtolower($m[3])==='minor'?'mineur':'majeur';
        return ($notes[$note]??$note).' '.$mode;
    }

    private function translateLabel(string $label,string $family): string
    {
        $key=mb_strtolower(trim($label));
        $maps=[
            'genre'=>['singer-songwriter'=>'auteur-compositeur-interprète','ballad'=>'ballade','french chanson'=>'chanson française','chanson française'=>'chanson française','folk'=>'folk','country'=>'country','soul'=>'soul','cabaret'=>'cabaret','world music'=>'musiques du monde'],
            'mood'=>['passionate'=>'passionnée','emotional'=>'émotionnelle','reflective'=>'introspective','intimate'=>'intime','somber'=>'sombre','dark'=>'sombre','longing'=>'empreinte de désir','romantic'=>'romantique','peaceful'=>'paisible','joyful'=>'joyeuse','energetic'=>'énergique'],
            'instrument'=>['string section'=>'section de cordes','violin'=>'violon','cello'=>'violoncelle','electric guitar'=>'guitare électrique','acoustic guitar'=>'guitare acoustique','bass guitar'=>'guitare basse','acoustic bass'=>'contrebasse','drum kit'=>'batterie','organ'=>'orgue','harmonica'=>'harmonica','mandolin'=>'mandoline','brass section'=>'section de cuivres'],
            'voice'=>['backing vocals'=>'voix d’accompagnement','powerful emotional singing'=>'chant puissant et émotionnel','soft intimate singing'=>'chant doux et intime','choir'=>'chœur','vocal harmonies'=>'harmonies vocales','raspy singing voice'=>'voix chantée rauque','female lead vocal'=>'voix principale féminine','male lead vocal'=>'voix principale masculine','instrumental music with no vocals'=>'caractère instrumental sans voix'],
            'audioset'=>['singing'=>'présence de chant','speech'=>'parole','guitar'=>'guitare','music'=>'musique'],
        ];
        return $maps[$family][$key]??$label;
    }
}
