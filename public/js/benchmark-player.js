(() => {
  "use strict";

  const audio = document.getElementById("master-audio");
  if (!audio) return;
  const audioAvailable = window.EZCHORDS_AUDIO_AVAILABLE === true;

  const playButton = document.getElementById("master-play");
  const stopButton = document.getElementById("master-stop");
  const mp3Enabled = document.getElementById("mp3-enabled");
  const state = document.getElementById("player-state");
  const synthState = document.getElementById("synth-state");
  const difficulty = document.getElementById("difficulty-level");
  const algoRadios = Array.from(document.querySelectorAll('input[name="listen_algo"]'));
  const rows = Array.from(document.querySelectorAll("[data-algo-row]"));

  let audioContext = null;
  let instrument = null;
  let instrumentPromise = null;
  let synthMode = "none";
  let selectedAlgo = 0;
  let lastBeatKey = null;
  let activeNodes = [];
  let raf = 0;
  let internalPlaying = false;
  let internalStartPerf = 0;
  let internalStartTime = 0;

  const NOTE_INDEX = {
    C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3,
    E: 4, Fb: 4, "E#": 5, F: 5, "F#": 6, Gb: 6,
    G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11, Cb: 11
  };
  const INDEX_NAME = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];

  function setState(text) {
    if (state) state.textContent = text;
  }

  function setSynthState(text) {
    if (synthState) synthState.textContent = "Synthé : " + text;
  }

  function nowTime() {
    if (audioAvailable) return audio.currentTime || 0;
    if (!internalPlaying) return internalStartTime;
    return internalStartTime + ((performance.now() - internalStartPerf) / 1000);
  }

  function isPlaying() {
    return audioAvailable ? !audio.paused : internalPlaying;
  }

  function playClock() {
    if (audioAvailable) {
      return audio.play();
    }
    if (!internalPlaying) {
      internalStartPerf = performance.now();
      internalPlaying = true;
    }
    return Promise.resolve();
  }

  function pauseClock() {
    if (audioAvailable) {
      audio.pause();
      return;
    }
    if (internalPlaying) {
      internalStartTime = nowTime();
      internalPlaying = false;
    }
  }

  function seekClock(t) {
    const value = Math.max(0, Number(t) || 0);
    if (audioAvailable) {
      audio.currentTime = value;
    } else {
      internalStartTime = value;
      if (internalPlaying) internalStartPerf = performance.now();
    }
  }

  function stopClock() {
    pauseClock();
    seekClock(0);
  }

  function selectedRow() {
    return rows.find(row => Number(row.dataset.algoRow) === selectedAlgo) || rows[0];
  }

  function allNotesOff() {
    for (const node of activeNodes) {
      try {
        if (node && typeof node.stop === "function") node.stop();
      } catch (_) {}
    }
    activeNodes = [];
  }

  function ensureInstrument() {
    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();

    if (instrument) {
      synthMode = "soundfont";
      return Promise.resolve(instrument);
    }

    // Immediate audible fallback: never block playback waiting for network.
    synthMode = "fallback";

    if (instrumentPromise) {
      return Promise.resolve(null);
    }

    setSynthState("fallback WebAudio actif · chargement SoundFont…");

    instrumentPromise = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/soundfont-player@0.12.0/dist/soundfont-player.min.js";
      script.async = true;

      script.onload = () => {
        if (!window.Soundfont) {
          setSynthState("fallback WebAudio actif");
          resolve(null);
          return;
        }

        window.Soundfont.instrument(
          audioContext,
          "acoustic_grand_piano",
          { soundfont: "MusyngKite" }
        ).then(inst => {
          instrument = inst;
          synthMode = "soundfont";
          setSynthState("SoundFont piano prêt");
          resolve(inst);
        }).catch(() => {
          synthMode = "fallback";
          setSynthState("fallback WebAudio actif");
          resolve(null);
        });
      };

      script.onerror = () => {
        synthMode = "fallback";
        setSynthState("fallback WebAudio actif");
        resolve(null);
      };

      document.head.appendChild(script);
    });

    return Promise.resolve(null);
  }


  function chordToNotes(label) {
    if (!label || label === "." || label === "N") return [];

    const slashMatch = label.match(/\/([357])$/);
    const inversionDegree = slashMatch ? Number(slashMatch[1]) : null;
    const cleaned = label.replace(/\/[357]$/, "");

    const m = cleaned.match(/^([A-G](?:#|b)?)(.*)$/);
    if (!m) return [];

    const rootName = m[1];
    const quality = m[2] || "";
    const root = NOTE_INDEX[rootName];
    if (root === undefined) return [];

    const level = difficulty ? difficulty.value : "intermediate";

    let intervals = [0, 4, 7];

    if (/^m(?!aj)/.test(quality)) intervals = [0, 3, 7];
    if (/dim/.test(quality)) intervals = [0, 3, 6];
    if (/sus2/.test(quality)) intervals = [0, 2, 7];
    if (/sus4/.test(quality)) intervals = [0, 5, 7];

    if (level !== "beginner") {
      if (/maj7/.test(quality)) intervals.push(11);
      else if (/m7/.test(quality) || /(^|[^a-z])7/.test(quality)) intervals.push(10);
    }

    // Débutant : triades uniquement.
    if (level === "beginner") {
      intervals = intervals.slice(0, 3);
    }

    // Confirmé : respecte les inversions /3, /5, /7 quand elles existent.
    if (level === "advanced" && inversionDegree) {
      const degreeToInterval = {
        3: /^m(?!aj)/.test(quality) ? 3 : 4,
        5: /dim/.test(quality) ? 6 : 7,
        7: /maj7/.test(quality) ? 11 : 10
      };
      const bassInterval = degreeToInterval[inversionDegree];
      if (bassInterval !== undefined) {
        intervals = [bassInterval - 12, ...intervals.filter(v => v !== bassInterval)];
      }
    }

    return intervals.map((interval, i) => {
      let semitone = root + interval;
      let octave = 4;

      while (semitone < 0) {
        semitone += 12;
        octave -= 1;
      }
      octave += Math.floor(semitone / 12);
      semitone = ((semitone % 12) + 12) % 12;

      // Keep the voicing compact around C4-C5.
      if (i > 0 && octave < 4) octave = 4;

      return INDEX_NAME[semitone] + octave;
    });
  }


  function timelineBeats(row) {
    const measures = Array.from(row.querySelectorAll(".measure"));
    const beats = [];
    let previousChord = null;
    let previousMeasureDuration = null;

    for (let i = 0; i < measures.length; i++) {
      const measure = measures[i];
      const beatEls = Array.from(measure.querySelectorAll(".beat"));
      if (!beatEls.length) continue;

      let start = Number(measure.dataset.start);
      if (!Number.isFinite(start)) start = 0;

      let nextStart = null;
      if (i + 1 < measures.length) {
        const candidate = Number(measures[i + 1].dataset.start);
        if (Number.isFinite(candidate) && candidate > start) nextStart = candidate;
      }

      let duration;
      if (nextStart !== null) {
        duration = nextStart - start;
        previousMeasureDuration = duration;
      } else if (previousMeasureDuration !== null) {
        duration = previousMeasureDuration;
      } else {
        duration = beatEls.length * 0.5;
      }

      const beatDuration = duration / beatEls.length;

      beatEls.forEach((el, beatIndex) => {
        const token = (el.dataset.token || "").trim();
        let chord = token;

        if (token === "-") chord = previousChord;
        else if (token === "." || token === "N" || token === "") chord = null;
        else previousChord = token;

        beats.push({
          key: `${measure.dataset.measure}:${beatIndex}`,
          start: start + beatIndex * beatDuration,
          end: start + (beatIndex + 1) * beatDuration,
          chord,
          el,
          measure
        });
      });
    }

    return beats;
  }

  function currentBeat(beats, t) {
    let lo = 0, hi = beats.length - 1, found = null;
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      const b = beats[mid];
      if (t < b.start) hi = mid - 1;
      else {
        found = b;
        lo = mid + 1;
      }
    }
    if (found && t < found.end + 0.03) return found;
    return found;
  }

  function clearHighlight() {
    document.querySelectorAll(".beat.current").forEach(el => el.classList.remove("current"));
    document.querySelectorAll(".measure.current-measure").forEach(el => el.classList.remove("current-measure"));
  }

  function highlightBeat(beat) {
    clearHighlight();
    if (!beat) return;

    beat.el.classList.add("current");
    beat.measure.classList.add("current-measure");

    const timeline = beat.el.closest(".timeline");
    if (!timeline) return;

    const left = beat.el.offsetLeft;
    const right = left + beat.el.offsetWidth;
    const visibleLeft = timeline.scrollLeft;
    const visibleRight = visibleLeft + timeline.clientWidth;

    if (left < visibleLeft + 80 || right > visibleRight - 80) {
      timeline.scrollTo({
        left: Math.max(0, left - Math.round(timeline.clientWidth * 0.30)),
        behavior: "smooth"
      });
    }
  }

  function noteNameToFrequency(note) {
    const m = String(note).match(/^([A-G]#?)(-?\d+)$/);
    if (!m) return null;
    const names = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11};
    const semitone = names[m[1]];
    if (semitone === undefined) return null;
    const octave = Number(m[2]);
    const midi = (octave + 1) * 12 + semitone;
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  function playFallback(notes, duration) {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    allNotesOff();

    const now = audioContext.currentTime;
    const stopAt = now + Math.max(0.08, Math.min(duration * 0.75, 0.55));

    activeNodes = notes.map(note => {
      const frequency = noteNameToFrequency(note);
      if (!frequency) return null;

      const osc = audioContext.createOscillator();
      const gain = audioContext.createGain();

      osc.type = "triangle";
      osc.frequency.value = frequency;

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.12, now + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, stopAt);

      osc.connect(gain);
      gain.connect(audioContext.destination);

      osc.start(now);
      osc.stop(stopAt + 0.02);

      return {
        stop: () => {
          try { osc.stop(); } catch (_) {}
        }
      };
    }).filter(Boolean);
  }

  async function strikeChord(chord, duration) {
    if (!chord) {
      allNotesOff();
      return;
    }

    const notes = chordToNotes(chord);
    if (!notes.length) return;

    try {
      ensureInstrument();

      if (audioContext && audioContext.state === "suspended") {
        await audioContext.resume();
      }

      if (synthMode === "soundfont" && instrument) {
        allNotesOff();
        const d = Math.max(0.08, Math.min(duration * 0.78, 0.65));
        activeNodes = notes.map(note => instrument.play(
          note,
          audioContext.currentTime,
          { duration: d, gain: 0.9 }
        )).filter(Boolean);
      } else {
        playFallback(notes, duration);
      }
    } catch (err) {
      synthMode = "fallback";
      playFallback(notes, duration);
      setSynthState("fallback WebAudio actif");
    }
  }


  function tick() {
    const row = selectedRow();
    if (!row) return;

    const beats = timelineBeats(row);
    const currentTime = nowTime();
    const beat = currentBeat(beats, currentTime);

    if (beat) {
      highlightBeat(beat);

      if (isPlaying() && beat.key !== lastBeatKey) {
        lastBeatKey = beat.key;
        strikeChord(beat.chord, beat.end - beat.start);
        setState(`${row.dataset.algoName} · ${beat.chord || "silence"} · ${currentTime.toFixed(2)} s`);
      }
    }

    raf = requestAnimationFrame(tick);
  }

  function selectAlgo(index) {
    selectedAlgo = Number(index);
    lastBeatKey = null;
    allNotesOff();
    clearHighlight();

    const radio = algoRadios.find(r => Number(r.value) === selectedAlgo);
    if (radio) radio.checked = true;

    const row = selectedRow();
    setState(row ? `Algorithme : ${row.dataset.algoName}` : "Algorithme sélectionné.");
  }

  algoRadios.forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.checked) selectAlgo(radio.value);
    });
  });

  document.querySelectorAll("[data-play-algo]").forEach(button => {
    button.addEventListener("click", () => {
      selectAlgo(button.dataset.playAlgo);

      if (!isPlaying()) {
        playClock()
          .then(() => setState("Lecture en cours."))
          .catch(err => setState("Erreur lecture audio : " + (err && err.message ? err.message : String(err))));
        playButton.textContent = "❚❚ Pause";
        ensureInstrument().catch(() => null);
      } else {
        pauseClock();
        playButton.textContent = "▶ Lire";
        allNotesOff();
      }
    });
  });

  mp3Enabled.addEventListener("change", () => {
    if (audioAvailable) audio.muted = !mp3Enabled.checked;
  });

  playButton.addEventListener("click", () => {
    if (!isPlaying()) {
      playClock()
        .then(() => setState("Lecture en cours."))
        .catch(err => setState("Erreur lecture audio : " + (err && err.message ? err.message : String(err))));
      playButton.textContent = "❚❚ Pause";
      ensureInstrument().catch(() => null);
    } else {
      pauseClock();
      playButton.textContent = "▶ Lire";
      allNotesOff();
    }
  });

  stopButton.addEventListener("click", () => {
    stopClock();
    playButton.textContent = "▶ Lire";
    lastBeatKey = null;
    allNotesOff();
    clearHighlight();
  });

  if (audioAvailable) audio.addEventListener("play", () => {
    playButton.textContent = "❚❚ Pause";
    lastBeatKey = null;
  });

  if (audioAvailable) audio.addEventListener("pause", () => {
    playButton.textContent = "▶ Lire";
    allNotesOff();
  });

  if (audioAvailable) audio.addEventListener("seeked", () => {
    lastBeatKey = null;
    allNotesOff();
  });

  if (audioAvailable) audio.addEventListener("ended", () => {
    lastBeatKey = null;
    allNotesOff();
    clearHighlight();
  });

  document.querySelectorAll(".beat").forEach(beatEl => {
    beatEl.addEventListener("click", () => {
      const row = beatEl.closest("[data-algo-row]");
      if (!row) return;

      selectAlgo(row.dataset.algoRow);

      const beats = timelineBeats(row);
      const target = beats.find(b => b.el === beatEl);
      if (!target) return;

      seekClock(target.start);
      lastBeatKey = null;
      highlightBeat(target);
    });
  });


  if (audioAvailable) {
    audio.addEventListener("error", () => {
      const mediaError = audio.error;
      setState("Erreur MP3" + (mediaError ? " (code " + mediaError.code + ")" : ""));
    });
    audio.addEventListener("canplay", () => {
      setState("MP3 prêt. Choisir un algorithme puis Lire.");
    });
  }

  if (difficulty) {
    difficulty.addEventListener("change", () => {
      const labels = {
        beginner: "Débutant",
        intermediate: "Intermédiaire",
        advanced: "Confirmé"
      };
      setState("Niveau de jeu : " + (labels[difficulty.value] || difficulty.value));
      lastBeatKey = null;
      allNotesOff();
    });
  }


  if (audioAvailable) {
    audio.addEventListener("loadedmetadata", () => {
      setState("MP3 prêt · durée " + audio.duration.toFixed(2) + " s");
    });
    audio.addEventListener("durationchange", () => {
      if (Number.isFinite(audio.duration) && audio.duration > 0) {
        setState("MP3 prêt · durée " + audio.duration.toFixed(2) + " s");
      }
    });
  }

  if (algoRadios.length) selectAlgo(algoRadios[0].value);
  if (audioAvailable) audio.muted = !mp3Enabled.checked;
  raf = requestAnimationFrame(tick);

  window.addEventListener("beforeunload", () => {
    cancelAnimationFrame(raf);
    allNotesOff();
  });
})();
