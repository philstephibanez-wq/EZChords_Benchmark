$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$template = Join-Path $repo "templates\workbench\profile.html.twig"

if (!(Test-Path $template)) { throw "Fichier introuvable: $template" }

$startMarker = "{% if selected_profile_run.state == 'done' and profile_validation_subjects %}"
$endMarker   = "{% set pv = selected_profile_run.diagnostics.profile_view ?? {} %}"

$t = Get-Content -Raw -Encoding UTF8 $template

$start = $t.IndexOf($startMarker)
$end   = $t.IndexOf($endMarker)

if ($start -lt 0) {
    throw "Borne de début introuvable. Aucun fichier modifié."
}
if ($end -lt 0) {
    throw "Borne de fin introuvable. Aucun fichier modifié."
}
if ($end -le $start) {
    throw "Ordre des bornes invalide. Aucun fichier modifié."
}

$backupDir = Join-Path $repo "var\tmp\profile_form_fr_r1e_backup"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
Copy-Item $template (Join-Path $backupDir "profile.html.twig") -Force

$newBlock = @'
{% if selected_profile_run.state == 'done' and profile_validation_subjects %}
<div class="card profile-human-validation">
  <div class="hero">
    <div>
      <h2>Validation humaine</h2>
      <div class="meta">
        Vérification musicale du run {{ selected_profile_run.public_id }}.
        Le formulaire valide les conclusions principales ; l’ADN conserve les données scientifiques et les scores d’origine.
        « Je ne sais pas » est une abstention humaine et n’est pas compté comme une erreur.
      </div>
    </div>
    <div class="meta">
      {{ profile_validation_stats.reviewed }} annoté(s) ·
      {{ profile_validation_stats.ok }} correct(s) ·
      {{ profile_validation_stats.ko }} incorrect(s) ·
      {{ profile_validation_stats.unknown }} sans avis
      {% if profile_validation_stats.accuracy is not null %}
        · précision sur avis connus {{ (profile_validation_stats.accuracy * 100)|number_format(1) }} %
      {% endif %}
    </div>
  </div>

  <form method="post"
        action="{{ path('profile_validate',{id:selected_profile_run.id}) }}"
        class="profile-human-validation-form">
    <table class="profile-validation-table">
      <thead>
        <tr>
          <th>Élément</th>
          <th>Proposition de l’analyse</th>
          <th>Votre avis</th>
          <th>Votre correction</th>
          <th>Degré de certitude</th>
          <th>Commentaire</th>
        </tr>
      </thead>
      <tbody>
      {% for subject in profile_validation_subjects %}
        {% set saved = profile_validations[subject.subject_key] ?? null %}

        {% set ui_label = {
          'tempo':'Tempo',
          'time_signature':'Mesure',
          'key':'Tonalité',
          'genre':'Genre',
          'instrumentation':'Instruments entendus',
          'voice':'Voix',
          'mood':'Ambiance',
          'audioset':'Éléments sonores remarquables',
          'choirs':'Chœurs / voix d’accompagnement'
        }[subject.item_key] ?? subject.label %}

        {% set ui_question = {
          'tempo':'Le tempo vous paraît-il correct ?',
          'time_signature':'La mesure vous paraît-elle correcte ?',
          'key':'La tonalité vous paraît-elle correcte ?',
          'genre':'Ce genre correspond-il bien au morceau ?',
          'instrumentation':'Ces instruments correspondent-ils à ce que vous entendez ?',
          'voice':'Cette description des voix vous paraît-elle correcte ?',
          'mood':'Cette ambiance correspond-elle au morceau ?',
          'audioset':'Ces éléments sonores vous paraissent-ils pertinents ?',
          'choirs':'Entendez-vous des chœurs ou des voix d’accompagnement ?'
        }[subject.item_key] ?? 'Cette proposition vous paraît-elle correcte ?' %}

        {% set ui_predicted = subject.predicted_text|replace({
          'singer-songwriter':'auteur-compositeur-interprète',
          'world music':'musiques du monde',
          'soft rock':'rock doux',
          'ballad':'ballade',
          'acoustic guitar':'guitare acoustique',
          'electric guitar':'guitare électrique',
          'bass guitar':'guitare basse',
          'acoustic bass':'contrebasse',
          'drum kit':'batterie',
          'snare drum':'caisse claire',
          'kick drum':'grosse caisse',
          'string section':'section de cordes',
          'brass section':'section de cuivres',
          'synthesizer':'synthétiseur',
          'keyboard (musical)':'clavier',
          'violin, fiddle':'violon',
          'violin':'violon',
          'cello':'violoncelle',
          'flute':'flûte',
          'clarinet':'clarinette',
          'ukulele':'ukulélé',
          'male lead vocal':'voix principale masculine',
          'female lead vocal':'voix principale féminine',
          'backing vocals':'voix d’accompagnement',
          'vocal harmonies':'harmonies vocales',
          'choir':'chœurs',
          'spoken voice':'voix parlée',
          'raspy singing voice':'voix chantée rauque',
          'vibrato singing':'chant avec vibrato',
          'powerful emotional singing':'chant puissant et expressif',
          'soft intimate singing':'chant doux et intimiste',
          'instrumental music with no vocals':'musique instrumentale sans voix',
          'vocal music':'musique vocale',
          'musical instrument':'instrument de musique',
          'singing':'chant',
          'speech':'parole',
          'reflective':'contemplatif',
          'intimate':'intimiste',
          'somber':'sombre',
          'passionate':'passionné',
          'mournful':'triste',
          'longing':'nostalgique',
          'dramatic':'dramatique',
          'romantic':'romantique',
          'melancholic':'mélancolique',
          'warm':'chaleureux',
          'dreamy':'rêveur',
          'nostalgic':'nostalgique',
          'tense':'tendu',
          'energetic':'énergique',
          'joyful':'joyeux',
          'peaceful':'paisible',
          'accepted':'retenu',
          'contextual':'contextuel',
          'generic':'générique',
          'uncertain':'incertain',
          'score':'indice'
        }) %}

        <tr>
          <td>
            <strong>{{ ui_label }}</strong>
            <div class="meta" style="margin-top:4px">{{ ui_question }}</div>
            <details style="margin-top:5px">
              <summary class="meta" style="cursor:pointer">Détails techniques</summary>
              <div class="meta">
                {{ subject.scope == 'gene' ? 'Gène' : 'Région' }}
                · {{ subject.subject_key }}
                {% if saved and saved.region_revision_ref %}
                  · {{ saved.region_revision_ref }}
                {% endif %}
                {% if saved and saved.gene_revision_ref %}
                  · {{ saved.gene_revision_ref }}
                {% endif %}
              </div>
            </details>
          </td>

          <td class="profile-machine-value">{{ ui_predicted }}</td>

          <td>
            <input type="hidden"
                   name="annotations[{{ loop.index0 }}][subject]"
                   value="{{ subject.subject_key }}">
            <div class="profile-verdicts" role="group" aria-label="Votre avis — {{ ui_label }}">
              <label>
                <input type="radio"
                       name="annotations[{{ loop.index0 }}][verdict]"
                       value="ok"
                       {{ saved and saved.verdict == 'ok' ? 'checked' : '' }}>
                Correct
              </label>
              <label>
                <input type="radio"
                       name="annotations[{{ loop.index0 }}][verdict]"
                       value="ko"
                       {{ saved and saved.verdict == 'ko' ? 'checked' : '' }}>
                Incorrect
              </label>
              <label>
                <input type="radio"
                       name="annotations[{{ loop.index0 }}][verdict]"
                       value="unknown"
                       {{ saved and saved.verdict == 'unknown' ? 'checked' : '' }}>
                Je ne sais pas
              </label>
            </div>
          </td>

          <td class="profile-human-truth">
            <input type="text"
                   name="annotations[{{ loop.index0 }}][human_value]"
                   value="{{ saved ? saved.human_value : '' }}"
                   placeholder="Valeur correcte si la proposition est incorrecte"
                   maxlength="500">

            {% if subject.item_key in ['instrumentation','voice','audioset','choirs'] %}
            <input type="text"
                   name="annotations[{{ loop.index0 }}][missing_expected]"
                   value="{{ saved ? saved.missing_expected_text : '' }}"
                   placeholder="Éléments entendus mais absents, séparés par ;"
                   maxlength="1000">
            {% endif %}
          </td>

          <td>
            <select name="annotations[{{ loop.index0 }}][reviewer_certainty]">
              <option value="" {{ not saved or not saved.reviewer_certainty ? 'selected' : '' }}>—</option>
              <option value="certain" {{ saved and saved.reviewer_certainty == 'certain' ? 'selected' : '' }}>Certain</option>
              <option value="probable" {{ saved and saved.reviewer_certainty == 'probable' ? 'selected' : '' }}>Probable</option>
              <option value="uncertain" {{ saved and saved.reviewer_certainty == 'uncertain' ? 'selected' : '' }}>Incertain</option>
            </select>
          </td>

          <td>
            <input type="text"
                   name="annotations[{{ loop.index0 }}][comment]"
                   value="{{ saved ? saved.comment : '' }}"
                   placeholder="Précision utile (facultatif)"
                   maxlength="2000">
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>

    <div style="margin-top:12px">
      <button type="submit">Enregistrer les annotations</button>
      <span class="meta">Les lignes sans avis sélectionné ne sont pas modifiées.</span>
    </div>
  </form>
</div>
{% endif %}

'@

$prefix = $t.Substring(0, $start)
$suffix = $t.Substring($end)
$out = $prefix + $newBlock + $suffix

# Vérifications avant écriture.
$required = @(
    "Validation humaine",
    "Proposition de l’analyse",
    "Votre avis",
    "Correct",
    "Incorrect",
    "Je ne sais pas",
    "'instrumentation':'Instruments entendus'",
    "'time_signature':'Mesure'",
    "{{ ui_predicted }}",
    $endMarker
)

foreach ($needle in $required) {
    if (!$out.Contains($needle)) {
        throw "Vérification finale échouée: $needle. Aucun fichier modifié."
    }
}

Set-Content -Path $template -Value $out -Encoding UTF8

# Nettoyage uniquement après succès.
$obsolete = @(
    "README_PROFILE_FORM_FR_R1.md",
    "README_PROFILE_FORM_FR_R1a_HOTFIX.md",
    "README_PROFILE_FORM_FR_R1b.md",
    "README_PROFILE_FORM_FR_R1c.md",
    "README_PROFILE_FORM_FR_R1d.md",
    "scripts\apply_profile_form_fr_r1.ps1",
    "scripts\apply_profile_form_fr_r1b.ps1",
    "scripts\apply_profile_form_fr_r1c.ps1",
    "scripts\apply_profile_form_fr_r1d.ps1",
    "scripts\test_profile_form_fr_r1.php",
    "scripts\test_profile_form_fr_r1b.php",
    "scripts\test_profile_form_fr_r1c.php",
    "scripts\test_profile_form_fr_r1d.php"
)
foreach ($rel in $obsolete) {
    $p = Join-Path $repo $rel
    if (Test-Path $p) { Remove-Item $p -Force }
}

Write-Host "PROFILE_FORM_FR_R1E_APPLIED"
Write-Host "Bloc Validation humaine remplace integralement"
Write-Host "Aucun PHP/Python modifie"
Write-Host "Scientific revision unchanged: R3B35C"
Write-Host "Backup: $backupDir"
