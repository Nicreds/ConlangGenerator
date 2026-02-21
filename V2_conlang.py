# ══════════════════════════════════════════════
# CONLANG GENERATOR V2 — Complete Implementation
# ══════════════════════════════════════════════
#
# pip install flask flask-session flask-wtf

from flask import (
    Flask, render_template_string, request,
    session, redirect, url_for, Response
)
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
import random
import re
import json
import uuid
import copy
import os
import datetime
from collections import Counter

# ──────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-999')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '.flask_sessions'
)
app.config['SESSION_PERMANENT'] = False
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
Session(app)
csrf = CSRFProtect(app)


# ──────────────────────────────────────────────
# ENGINE
# ──────────────────────────────────────────────

class LinguisticEngine:

    def __init__(self):
        self.defaults = {
            "vowels": "aeiou",
            "consonants": "ptkmnls",
            "structures": ["CV", "CVC", "VC"],
            "tones": [],
            "min_syl": 2,
            "max_syl": 3,
            "morphology": {
                "Masculine": {
                    "mode": "simple", "pre": "", "suf": "os",
                    "pattern": "", "replacement": "",
                },
                "Feminine": {
                    "mode": "simple", "pre": "", "suf": "a",
                    "pattern": "", "replacement": "",
                },
            },
            "derivations": {
                "Verb": {
                    "mode": "simple", "pre": "", "suf": "en",
                    "pattern": "", "replacement": "",
                },
                "Agent": {
                    "mode": "simple", "pre": "", "suf": "ar",
                    "pattern": "", "replacement": "",
                },
            },
            "forbidden_clusters": [],
            "vowel_harmony": False,
            "harmony_groups": {"front": "eiy", "back": "aou"},
            "phoneme_weights": {},
            "ipa_map": {},
            "categories": [
                "General", "Nature", "Body", "Emotion",
                "Abstract", "Action", "Object", "Social",
            ],
            "sound_changes": [],
        }

    def get_defaults(self):
        return copy.deepcopy(self.defaults)

    def analyze_corpus(self, text):
        if not text or not text.strip():
            return None, None, {}
        clean = re.sub(r'[^a-zA-Z]', '', text.lower())
        if not clean:
            return None, None, {}
        freq = Counter(clean)
        vowel_set = set("aeiouy")
        v = sorted({c for c in clean if c in vowel_set})
        c = sorted({c for c in clean if c not in vowel_set})
        mx = max(freq.values()) if freq else 1
        weights = {
            ch: max(1, round((cnt / mx) * 10))
            for ch, cnt in freq.items()
        }
        return "".join(v) or None, "".join(c) or None, weights

    @staticmethod
    def validate_euphony(word, vowels="aeiouy", forbidden=None):
        if not word:
            return False
        esc = re.escape(vowels)
        if re.search(rf'[{esc}]{{3,}}', word):
            return False
        if re.search(rf'[^{esc}]{{3,}}', word):
            return False
        if forbidden:
            wl = word.lower()
            for cl in forbidden:
                if cl.lower() in wl:
                    return False
        return True

    @staticmethod
    def check_harmony(word, groups, vowels_str):
        front = set(groups.get("front", ""))
        back = set(groups.get("back", ""))
        vw = [c for c in word if c in vowels_str]
        if not vw:
            return True
        return not (
            any(v in front for v in vw) and
            any(v in back for v in vw)
        )

    def apply_morphology(self, root, rule):
        if not rule:
            return root
        mode = rule.get('mode', 'simple')
        if mode == 'regex':
            pattern = rule.get('pattern', '')
            repl = rule.get('replacement', '')
            if not pattern or len(pattern) > 300:
                return root
            try:
                result = re.sub(pattern, repl, root)
                return result if result else root
            except re.error:
                return root
        else:
            pre = rule.get('pre', '') or ''
            suf = rule.get('suf', '') or ''
            return f"{pre}{root}{suf}"

    @staticmethod
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return LinguisticEngine.levenshtein(s2, s1)
        if not s2:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(
                    prev[j + 1] + 1, curr[j] + 1,
                    prev[j] + (c1 != c2),
                ))
            prev = curr
        return prev[-1]

    def find_similar(self, word, dictionary, threshold=2):
        out = []
        for e in dictionary:
            d = self.levenshtein(word.lower(), e['word'].lower())
            if 0 < d <= threshold:
                out.append({
                    "word": e['word'],
                    "meaning": e['meaning'],
                    "distance": d,
                })
        return out

    @staticmethod
    def apply_sound_changes(word, rules):
        r = word
        for rule in rules:
            src = rule.get('from', '')
            tgt = rule.get('to', '')
            ctx = rule.get('context', '_')
            if not src:
                continue
            if ctx == '_':
                r = r.replace(src, tgt)
            elif ctx == '#_' and r.startswith(src):
                r = tgt + r[len(src):]
            elif ctx == '_#' and r.endswith(src):
                r = r[:-len(src)] + tgt
            elif ctx == 'V_V':
                pat = (r'([aeiouy])' + re.escape(src) + r'([aeiouy])')
                r = re.sub(pat, r'\1' + tgt + r'\2', r)
        return r

    @staticmethod
    def to_ipa(word, ipa_map):
        if not ipa_map:
            return ""
        r = word.lower()
        for g in sorted(ipa_map, key=len, reverse=True):
            r = r.replace(g, ipa_map[g])
        return f"/{r}/"

    def derive_word(self, source, deriv_key, config):
        rule = config.get('derivations', {}).get(deriv_key)
        if not rule:
            return None
        root = source.get('root', source.get('word', ''))
        derived = self.apply_morphology(root, rule)
        return {
            "id": str(uuid.uuid4()),
            "word": derived,
            "root": root,
            "class": deriv_key,
            "meaning": f"{source['meaning']} ({deriv_key})",
            "category": source.get('category', 'General'),
            "tone": source.get('tone', ''),
            "derived_from": source.get('id', ''),
            "ipa": "",
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        }

    def generate_batch(self, config, meaning, class_key,
                       count=8, category="General"):

        vowels_str = config.get('vowels') or self.defaults['vowels']
        cons_str = config.get('consonants') or self.defaults['consonants']
        vowels = list(vowels_str)
        consonants = list(cons_str)
        structures = config.get('structures') or self.defaults['structures']
        tones = config.get('tones') or []
        forbidden = config.get('forbidden_clusters') or []
        harmony_on = config.get('vowel_harmony', False)
        h_groups = config.get(
            'harmony_groups', self.defaults['harmony_groups']
        )
        weights = config.get('phoneme_weights', {})
        sc = config.get('sound_changes', [])

        if not vowels or not consonants or not structures:
            return []

        v_w = [weights.get(v, 5) for v in vowels]
        c_w = [weights.get(c, 5) for c in consonants]

        morph_rule = None
        display_class = ""
        if class_key and class_key != '__none__':
            morph_rule = config.get('morphology', {}).get(class_key)
            display_class = class_key

        min_s = max(1, int(config.get('min_syl', 2)))
        max_s = max(min_s, int(config.get('max_syl', 3)))

        candidates = []
        seen = set()
        att = 0

        while len(candidates) < count and att < count * 40:
            att += 1
            root = ""
            nsyl = random.randint(min_s, max_s)

            if harmony_on:
                fv = [v for v in vowels
                      if v in h_groups.get('front', '')]
                bv = [v for v in vowels
                      if v in h_groups.get('back', '')]
                if fv and bv:
                    cv = random.choice([fv, bv])
                else:
                    cv = fv or bv or vowels
                cvw = [weights.get(v, 5) for v in cv]
            else:
                cv = vowels
                cvw = v_w

            for _ in range(nsyl):
                st = random.choice(structures)
                for ch in st.upper():
                    if ch == 'C':
                        root += random.choices(
                            consonants, weights=c_w, k=1
                        )[0]
                    elif ch == 'V':
                        root += random.choices(
                            cv, weights=cvw, k=1
                        )[0]

            if sc:
                root = self.apply_sound_changes(root, sc)

            if not self.validate_euphony(root, vowels_str, forbidden):
                continue

            if harmony_on and not self.check_harmony(
                root, h_groups, vowels_str
            ):
                continue

            if morph_rule:
                full = self.apply_morphology(root, morph_rule)
            else:
                full = root

            if full in seen:
                continue
            seen.add(full)

            tone_val = random.choice(tones) if tones else ""
            ipa = self.to_ipa(full, config.get('ipa_map', {}))

            candidates.append({
                "id": str(uuid.uuid4()),
                "word": full,
                "root": root,
                "ipa": ipa,
                "tone": tone_val,
                "class": display_class,
                "meaning": meaning,
                "category": category,
                "derived_from": "",
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            })

        return candidates


engine = LinguisticEngine()


# ──────────────────────────────────────────────
# HTML TEMPLATE
# ──────────────────────────────────────────────

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Conlang Generator V2</title>
<style>
/* ── Light Theme (default) ── */
:root {
    --bg-body: #f4f6f7;
    --bg-panel: #ffffff;
    --bg-sidebar: #ffffff;
    --bg-header: #2c3e50;
    --bg-tabbar: #34495e;
    --bg-input: #ffffff;
    --bg-light: #ecf0f1;
    --bg-workspace: #f8f9fa;
    --bg-card: #ffffff;
    --bg-stat: #ecf0f1;
    --bg-sample: #f8f9fa;

    --text-primary: #333333;
    --text-secondary: #555555;
    --text-muted: #999999;
    --text-header: #ffffff;
    --text-word: #2c3e50;

    --brd: #bdc3c7;
    --brd-focus: #2980b9;

    --pri: #2c3e50;
    --sec: #34495e;
    --acc: #2980b9;
    --ok: #27ae60;
    --err: #c0392b;
    --warn: #f39c12;
    --purp: #8e44ad;
}

/* ── Dark Theme ── */
[data-theme="dark"] {
    --bg-body: #1a1a2e;
    --bg-panel: #16213e;
    --bg-sidebar: #0f3460;
    --bg-header: #0a0a1a;
    --bg-tabbar: #0f1a30;
    --bg-input: #1a1a3e;
    --bg-light: #1e2a4a;
    --bg-workspace: #12122a;
    --bg-card: #16213e;
    --bg-stat: #1e2a4a;
    --bg-sample: #1a1a3e;

    --text-primary: #e0e0e0;
    --text-secondary: #b0b0b0;
    --text-muted: #777777;
    --text-header: #e0e0e0;
    --text-word: #6cb4ee;

    --brd: #2a3a5a;
    --brd-focus: #4a9edd;

    --pri: #6cb4ee;
    --sec: #8899bb;
    --acc: #4a9edd;
}

* { box-sizing: border-box; }

body {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg-body);
    color: var(--text-primary);
    margin: 0; padding: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.3s, color 0.3s;
}

header {
    background: var(--bg-header);
    color: var(--text-header);
    padding: 12px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 4px solid var(--acc);
}
.brand {
    font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; font-size: 1.1rem;
}
.brand span { font-weight: 300; opacity: .7; }
.hdr-r { display: flex; align-items: center; gap: 15px; }
.hdr-r .status { font-size: .75rem; opacity: .8; }

/* Night Mode Toggle */
.night-toggle {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    color: var(--text-header);
    padding: 5px 12px;
    border-radius: 20px;
    cursor: pointer;
    font-size: .75rem;
    font-weight: 600;
    width: auto;
    margin: 0;
    transition: 0.2s;
    text-transform: none;
    display: flex;
    align-items: center;
    gap: 5px;
}
.night-toggle:hover {
    background: rgba(255,255,255,0.25);
}

.tab-bar {
    background: var(--bg-tabbar);
    display: flex; padding: 0 25px;
}
.tab-btn {
    background: none; border: none;
    color: rgba(255,255,255,.55);
    padding: 10px 20px; cursor: pointer;
    font-size: .8rem; text-transform: uppercase;
    font-weight: 600;
    border-bottom: 3px solid transparent;
    margin: 0; width: auto;
    transition: .2s; border-radius: 0;
}
.tab-btn:hover { color: #fff; }
.tab-btn.active {
    color: #fff;
    border-bottom-color: var(--acc);
    background: rgba(255,255,255,.05);
}
.tab-content { display: none; }
.tab-content.active { display: block; }

.layout {
    display: grid;
    grid-template-columns: 370px 1fr;
    flex: 1; overflow: hidden;
}

.sidebar {
    background: var(--bg-sidebar);
    border-right: 1px solid var(--brd);
    padding: 15px; overflow-y: auto;
    transition: background 0.3s;
}

h2 {
    font-size: .85rem; color: var(--sec);
    text-transform: uppercase;
    border-bottom: 2px solid var(--bg-light);
    padding-bottom: 5px; margin-top: 20px;
}
h2:first-child { margin-top: 0; }

label {
    display: block; font-size: .78rem;
    font-weight: 600; margin-top: 8px;
    color: var(--text-secondary);
}

input[type="text"], input[type="number"], textarea, select {
    width: 100%; padding: 7px; margin-top: 3px;
    border: 1px solid var(--brd);
    border-radius: 3px;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: .85rem;
    background: var(--bg-input);
    color: var(--text-primary);
    transition: background 0.3s, color 0.3s, border-color 0.3s;
}
input:focus, select:focus, textarea:focus {
    border-color: var(--brd-focus); outline: none;
}

button {
    padding: 8px 12px; border: none;
    background: var(--sec); color: #fff;
    font-weight: 600; cursor: pointer;
    border-radius: 3px; margin-top: 10px;
    text-transform: uppercase;
    font-size: .75rem; transition: .2s; width: 100%;
}
button:hover { background: var(--acc); }
.act-btn { background: var(--ok); padding: 12px; font-size: .85rem; }
.err-btn {
    background: var(--err); width: auto;
    padding: 5px 10px; margin: 0; font-size: .7rem;
}
.ico-btn {
    background: transparent; color: var(--text-primary);
    border: 1px solid var(--brd);
    width: auto; margin: 0; padding: 5px 10px;
}
.der-btn {
    background: var(--purp); width: auto;
    padding: 4px 8px; margin: 0; font-size: .65rem;
}

.workspace {
    padding: 25px; overflow-y: auto;
    background: var(--bg-workspace);
    transition: background 0.3s;
}
.panel {
    background: var(--bg-panel);
    border: 1px solid var(--brd);
    border-radius: 4px; padding: 18px;
    margin-bottom: 18px;
    box-shadow: 0 2px 5px rgba(0,0,0,.05);
    transition: background 0.3s, border-color 0.3s;
}

.batch-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px; margin-top: 12px;
}
.ccard {
    background: var(--bg-card);
    border: 1px solid var(--brd);
    padding: 12px; text-align: center;
    border-radius: 4px; transition: .2s;
    color: var(--text-primary);
}
.ccard:hover {
    border-color: var(--acc);
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,.1);
}
.wdisp {
    font-size: 1.25rem; font-weight: bold;
    color: var(--text-word); margin-bottom: 3px;
}
.wipa { font-size: .8rem; color: var(--acc); font-style: italic; }
.wmeta { font-size: .72rem; color: var(--text-muted); margin-top: 3px; }
.wtone {
    display: inline-block; background: #fff3cd;
    color: #856404; border: 1px solid #ffc107;
    padding: 1px 6px; border-radius: 3px;
    font-size: .7rem; margin-top: 4px;
}
.sim-warn {
    background: #fff3cd; border: 1px solid #ffc107;
    color: #856404; padding: 4px 8px;
    border-radius: 3px; font-size: .7rem; margin-top: 5px;
}

table {
    width: 100%; border-collapse: collapse;
    margin-top: 10px; font-size: .85rem;
}
th {
    text-align: left; background: var(--bg-light);
    padding: 8px 10px;
    border-bottom: 2px solid var(--brd);
    font-size: .78rem; color: var(--text-secondary);
}
td {
    padding: 8px 10px;
    border-bottom: 1px solid var(--brd);
    color: var(--text-primary);
}
.badge {
    background: var(--bg-light); padding: 2px 6px;
    border-radius: 3px; font-size: .72rem;
    border: 1px solid var(--brd);
    color: var(--text-secondary);
}
.badge-cat {
    background: #eaf2f8; border-color: var(--acc);
    color: var(--acc);
}
.badge-der {
    background: #f4ecf7; border-color: var(--purp);
    color: var(--purp);
}
.badge-rx {
    background: #fdf2e9; border-color: var(--warn);
    color: #e67e22; font-family: monospace;
}
.badge-tone {
    background: #fff3cd; border-color: #ffc107; color: #856404;
}

.fr { display: flex; gap: 8px; }
.fa {
    display: flex; justify-content: space-between;
    align-items: center;
}
.flash {
    padding: 8px 15px; border-radius: 3px;
    margin-bottom: 15px; font-size: .85rem;
}
.flash-ok {
    background: #d4edda; color: #155724;
    border: 1px solid #c3e6cb;
}
.flash-err {
    background: #f8d7da; color: #721c24;
    border: 1px solid #f5c6cb;
}
.flash-warn {
    background: #fff3cd; color: #856404;
    border: 1px solid #ffc107;
}
.help { font-size: .7rem; color: var(--text-muted); margin-top: 2px; }

.tgl-row {
    display: flex; align-items: center;
    gap: 8px; margin-top: 8px;
}
.tgl-row input[type="checkbox"] { width: auto; margin: 0; }

.search-bar {
    width: 100%; padding: 8px 12px;
    border: 1px solid var(--brd);
    border-radius: 3px; margin-bottom: 10px;
    font-size: .85rem;
    background: var(--bg-input);
    color: var(--text-primary);
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px; margin-bottom: 15px;
}
.stat-card {
    background: var(--bg-stat); padding: 12px;
    border-radius: 4px; text-align: center;
    transition: background 0.3s;
}
.stat-card .num {
    font-size: 1.5rem; font-weight: bold;
    color: var(--text-word);
}
.stat-card .lbl {
    font-size: .7rem; color: var(--text-muted);
    text-transform: uppercase;
}

.mode-select {
    display: flex; gap: 5px; margin-top: 5px;
}
.mode-select label {
    font-size: .72rem; margin: 0;
    display: flex; align-items: center; gap: 3px;
}
.mode-select input[type="radio"] { width: auto; margin: 0; }
.regex-fields, .simple-fields { margin-top: 5px; }

.sample-box {
    background: var(--bg-sample);
    border: 1px solid var(--brd);
    border-radius: 3px;
    padding: 10px; margin-top: 5px; margin-bottom: 8px;
    transition: background 0.3s, border-color 0.3s;
}
.sample-box textarea {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: .85rem;
    background: var(--bg-input);
    color: var(--text-primary);
    border: 1px solid var(--brd);
    border-radius: 3px;
    padding: 8px;
    resize: vertical;
    min-height: 80px;
    line-height: 1.5;
}
.sample-label {
    font-size: .75rem; color: var(--acc);
    font-weight: 600; margin-bottom: 5px;
}

/* Disabled button style */
button:disabled, button[disabled] {
    opacity: 0.4;
    cursor: not-allowed;
}
button:disabled:hover, button[disabled]:hover {
    background: var(--sec);
}
</style>
</head>
<body>

<header>
    <div class="brand">Conlang Generator <span>| V2</span></div>
    <div class="hdr-r">
        <div class="status">Lexicon: {{ dictionary|length }} entries</div>
        <button class="night-toggle" onclick="toggleTheme()" id="theme-btn">
            <span id="theme-icon">🌙</span>
            <span id="theme-label">Night View</span>
        </button>
    </div>
</header>

<div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('generate')">Generate</button>
    <button class="tab-btn" onclick="switchTab('lexicon')">Lexicon</button>
    <button class="tab-btn" onclick="switchTab('tools')">Tools</button>
</div>

<div class="layout">

<!-- ═══ SIDEBAR ═══ -->
<div class="sidebar">
    <form method="POST" action="/update_config">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <h2>1. Phonemic Inventory</h2>

        <div class="sample-box">
            <div class="sample-label">📝 Sample Text for Analysis</div>
            <textarea name="corpus" rows="4"
                placeholder="Type or paste any sample text here. When you click 'Update Standards' below, phonemes and frequency weights will be automatically extracted from this text.

Example: The quick brown fox jumps over the lazy dog.

Leave this empty to use the manual vowel/consonant values below instead.">{{ session_corpus }}</textarea>
            <div class="help" style="margin-top:5px;">
                Analyzed when you press <strong>Update Standards</strong>.
                Manual values below are overridden when text is present.
            </div>
        </div>

        <label>Vowels (V)</label>
        <input type="text" name="vowels" value="{{ config.vowels }}">

        <label>Consonants (C)</label>
        <input type="text" name="consonants" value="{{ config.consonants }}">

        <label>Tones (comma-separated labels)</label>
        <input type="text" name="tones" value="{{ config.tones|join(',') }}"
               placeholder="e.g. High,Low,Rising,Falling">
        <div class="help">Assigned as metadata, not appended to words.</div>

        <label>Forbidden Clusters</label>
        <input type="text" name="forbidden_clusters"
               value="{{ config.forbidden_clusters|join(',') }}"
               placeholder="e.g. tk,pm,ss">

        <h2>2. Structural Logic</h2>

        <label>Permitted Syllables</label>
        <input type="text" name="structures"
               value="{{ config.structures|join(',') }}"
               placeholder="e.g. CV,CVC,VC">

        <label>Syllable Count Range</label>
        <div class="fr">
            <input type="number" name="min_syl" value="{{ config.min_syl }}" min="1" max="10">
            <input type="number" name="max_syl" value="{{ config.max_syl }}" min="1" max="10">
        </div>

        <div class="tgl-row">
            <input type="checkbox" name="vowel_harmony" id="vh"
                   {{ 'checked' if config.vowel_harmony else '' }}>
            <label for="vh" style="margin:0;">Vowel Harmony</label>
        </div>
        <div class="help">Front/back vowels cannot mix within one word</div>
        <div class="fr" style="margin-top:5px;">
            <div><label style="font-size:.7rem;">Front</label>
                <input type="text" name="harmony_front"
                       value="{{ config.harmony_groups.front }}"></div>
            <div><label style="font-size:.7rem;">Back</label>
                <input type="text" name="harmony_back"
                       value="{{ config.harmony_groups.back }}"></div>
        </div>

        <button type="submit">Update Standards</button>
    </form>

    <!-- MORPHOLOGICAL CLASSES -->
    <h2>3. Morphological Classes</h2>
    <div class="help" style="margin-bottom:8px;">
        Define inflection patterns. Use "None" during generation to skip.
        Supports simple prefix/suffix or regex mode.
    </div>
    <form method="POST" action="/add_class">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="text" name="c_name" placeholder="Class Name (e.g. Divine)" required>
        <div class="mode-select">
            <label><input type="radio" name="c_mode" value="simple" checked
                onchange="document.getElementById('cls_simple').style.display='block';
                          document.getElementById('cls_regex').style.display='none';">
                Simple</label>
            <label><input type="radio" name="c_mode" value="regex"
                onchange="document.getElementById('cls_regex').style.display='block';
                          document.getElementById('cls_simple').style.display='none';">
                Regex</label>
        </div>
        <div id="cls_simple" class="simple-fields">
            <div class="fr">
                <input type="text" name="c_pre" placeholder="Prefix">
                <input type="text" name="c_suf" placeholder="Suffix">
            </div>
        </div>
        <div id="cls_regex" class="regex-fields" style="display:none;">
            <label style="font-size:.7rem;">Pattern (applied to root)</label>
            <input type="text" name="c_pattern" placeholder="e.g. (.+)">
            <label style="font-size:.7rem;">Replacement</label>
            <input type="text" name="c_replacement" placeholder='e.g. \1os'>
            <div class="help">Uses Python re.sub(pattern, replacement, root)</div>
        </div>
        <button type="submit" class="ico-btn"
                style="width:100%;margin-top:5px;background:var(--bg-light);">
            + Add Class</button>
    </form>

    <div style="margin-top:10px;">
        {% for name, r in config.morphology.items() %}
        <div class="fa" style="font-size:.78rem;padding:4px 0;border-bottom:1px dashed var(--brd);">
            <span>
                <strong>{{ name }}</strong>
                {% if r.mode == 'regex' %}
                    <span class="badge badge-rx">regex</span>
                    <span style="color:var(--text-muted);font-size:.7rem;">
                        {{ r.pattern }} → {{ r.replacement }}</span>
                {% else %}
                    <span style="color:var(--text-muted);">
                        ({{ r.pre }}...{{ r.suf }})</span>
                {% endif %}
            </span>
            <form action="/remove_class" method="POST" style="margin:0;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="name" value="{{ name }}">
                <button type="submit"
                    style="background:none;color:var(--err);border:none;padding:0;
                           margin:0;cursor:pointer;width:auto;">&times;</button>
            </form>
        </div>
        {% else %}
        <div class="help" style="padding:5px 0;">
            No classes defined. Words will be generated as bare roots.
        </div>
        {% endfor %}
    </div>

    <!-- DERIVATION RULES -->
    <h2>4. Derivation Rules</h2>
    <div class="help" style="margin-bottom:8px;">
        Create word families from existing entries. Supports simple or regex.
    </div>
    <form method="POST" action="/add_derivation">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="text" name="d_name" placeholder="Type (e.g. Diminutive)" required>
        <div class="mode-select">
            <label><input type="radio" name="d_mode" value="simple" checked
                onchange="document.getElementById('der_simple').style.display='block';
                          document.getElementById('der_regex').style.display='none';">
                Simple</label>
            <label><input type="radio" name="d_mode" value="regex"
                onchange="document.getElementById('der_regex').style.display='block';
                          document.getElementById('der_simple').style.display='none';">
                Regex</label>
        </div>
        <div id="der_simple" class="simple-fields">
            <div class="fr">
                <input type="text" name="d_pre" placeholder="Prefix">
                <input type="text" name="d_suf" placeholder="Suffix">
            </div>
        </div>
        <div id="der_regex" class="regex-fields" style="display:none;">
            <label style="font-size:.7rem;">Pattern</label>
            <input type="text" name="d_pattern" placeholder="e.g. (.+)">
            <label style="font-size:.7rem;">Replacement</label>
            <input type="text" name="d_replacement" placeholder='e.g. \1ling'>
        </div>
        <button type="submit" class="ico-btn"
                style="width:100%;margin-top:5px;background:#f4ecf7;">
            + Add Derivation</button>
    </form>

    <div style="margin-top:10px;">
        {% for name, r in config.derivations.items() %}
        <div class="fa" style="font-size:.78rem;padding:4px 0;border-bottom:1px dashed var(--brd);">
            <span>
                <strong>{{ name }}</strong>
                {% if r.mode == 'regex' %}
                    <span class="badge badge-rx">regex</span>
                    <span style="color:var(--text-muted);font-size:.7rem;">
                        {{ r.pattern }} → {{ r.replacement }}</span>
                {% else %}
                    <span style="color:var(--text-muted);">
                        ({{ r.pre }}...{{ r.suf }})</span>
                {% endif %}
            </span>
            <form action="/remove_derivation" method="POST" style="margin:0;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="name" value="{{ name }}">
                <button type="submit"
                    style="background:none;color:var(--err);border:none;padding:0;
                           margin:0;cursor:pointer;width:auto;">&times;</button>
            </form>
        </div>
        {% else %}
        <div class="help" style="padding:5px 0;">No derivation rules defined.</div>
        {% endfor %}
    </div>
</div>

<!-- ═══ WORKSPACE ═══ -->
<div class="workspace">

    {% if flash_msg %}
    <div class="flash {{ 'flash-ok' if flash_type == 'ok' else '' }}
                       {{ 'flash-err' if flash_type == 'error' else '' }}
                       {{ 'flash-warn' if flash_type == 'warning' else '' }}">
        {{ flash_msg }}
    </div>
    {% endif %}

    <!-- TAB: GENERATE -->
    <div class="tab-content active" id="tab-generate">
        <div class="panel">
            <div class="fa">
                <h2 style="margin:0;border:none;">Generation Protocol</h2>
                <form action="/clear_batch" method="POST" style="margin:0;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit" class="ico-btn">Clear</button>
                </form>
            </div>

            <form method="POST" action="/generate">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="fr" style="align-items:flex-end;flex-wrap:wrap;">
                    <div style="flex:2;min-width:150px;">
                        <label>Target Concept</label>
                        <input type="text" name="meaning"
                               placeholder="e.g. Order" required>
                    </div>
                    <div style="flex:1;min-width:120px;">
                        <label>Class</label>
                        <select name="class_key">
                            <option value="__none__">— None —</option>
                            {% for k in config.morphology.keys() %}
                            <option value="{{ k }}">{{ k }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div style="flex:1;min-width:120px;">
                        <label>Category</label>
                        <select name="category">
                            {% for cat in config.categories %}
                            <option value="{{ cat }}">{{ cat }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div style="flex:.5;min-width:80px;">
                        <label>Count</label>
                        <input type="number" name="count"
                               value="8" min="1" max="20">
                    </div>
                </div>
                <button type="submit" class="act-btn">Generate Candidates</button>
            </form>

            {% if batch %}
            <div style="margin-top:18px;border-top:2px solid var(--brd);padding-top:12px;">
                <div class="fa">
                    <span style="font-size:.85rem;font-weight:bold;color:var(--sec);">
                        Candidates for: "{{ batch[0].meaning }}"
                        {% if batch[0].class %}
                        <span class="badge">{{ batch[0].class }}</span>
                        {% endif %}
                        <span class="badge badge-cat">{{ batch[0].category }}</span>
                    </span>
                    <form action="/approve_all" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="ico-btn"
                                style="color:var(--ok);border-color:var(--ok);">
                            Approve All</button>
                    </form>
                </div>

                <div class="batch-grid">
                    {% for item in batch %}
                    <form action="/approve_one" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="id" value="{{ item.id }}">
                        <button type="submit" class="ccard"
                                style="width:100%;margin:0;cursor:pointer;">
                            <div class="wdisp">{{ item.word }}</div>
                            {% if item.ipa %}
                            <div class="wipa">{{ item.ipa }}</div>
                            {% endif %}
                            {% if item.tone %}
                            <div class="wtone">{{ item.tone }}</div>
                            {% endif %}
                            <div class="wmeta">
                                {% if item.class %}{{ item.class }} | {% endif %}
                                Root: {{ item.root }}
                            </div>
                            {% if item.similar %}
                            <div class="sim-warn">
                                ⚠ Similar: {{ item.similar|join(', ') }}
                            </div>
                            {% endif %}
                            <div style="margin-top:6px;font-size:.7rem;
                                        color:var(--ok);font-weight:bold;">
                                [ APPROVE ]
                            </div>
                        </button>
                    </form>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- TAB: LEXICON -->
    <div class="tab-content" id="tab-lexicon">
        <div class="stat-grid">
            <div class="stat-card">
                <div class="num">{{ dictionary|length }}</div>
                <div class="lbl">Words</div>
            </div>
            <div class="stat-card">
                <div class="num">{{ stats.classes }}</div>
                <div class="lbl">Classes</div>
            </div>
            <div class="stat-card">
                <div class="num">{{ stats.categories }}</div>
                <div class="lbl">Categories</div>
            </div>
            <div class="stat-card">
                <div class="num">{{ stats.derived }}</div>
                <div class="lbl">Derived</div>
            </div>
        </div>

        <div class="panel">
            <div class="fa">
                <h2 style="margin:0;border:none;">Approved Lexicon</h2>
                <div class="fr">
                    <a href="/export" style="text-decoration:none;">
                        <button type="button" class="ico-btn">Export JSON</button>
                    </a>
                    <form action="/save_project" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="ico-btn"
                                style="color:var(--acc);border-color:var(--acc);">
                            💾 Save Project</button>
                    </form>
                    <form action="/purge_dict" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="err-btn">Purge</button>
                    </form>
                </div>
            </div>

            <input type="text" class="search-bar" id="search-input"
                   placeholder="Search by word or meaning..."
                   onkeyup="filterTable()">
            <div style="margin-bottom:8px;">
                <select id="filter-cat" onchange="filterTable()"
                        style="width:auto;padding:4px 8px;font-size:.8rem;">
                    <option value="">All Categories</option>
                    {% for cat in config.categories %}
                    <option value="{{ cat }}">{{ cat }}</option>
                    {% endfor %}
                </select>
            </div>

            <table id="lex-table">
                <thead><tr>
                    <th>Concept</th><th>Class</th><th>Category</th>
                    <th>Word</th><th>IPA</th><th>Tone</th>
                    <th>Derive</th><th></th>
                </tr></thead>
                <tbody>
                {% for e in dictionary %}
                <tr data-word="{{ e.word|lower }}"
                    data-meaning="{{ e.meaning|lower }}"
                    data-cat="{{ e.category|default('General') }}">
                    <td>{{ e.meaning }}</td>
                    <td>{% if e.class %}<span class="badge">{{ e.class }}</span>
                        {% else %}—{% endif %}</td>
                    <td>
                        <span class="badge badge-cat">
                            {{ e.category|default('General') }}</span>
                        {% if e.derived_from %}
                        <span class="badge badge-der">derived</span>
                        {% endif %}
                    </td>
                    <td style="font-weight:bold;color:var(--text-word);">
                        {{ e.word }}</td>
                    <td style="color:var(--acc);">{{ e.ipa|default('') }}</td>
                    <td>{% if e.tone %}
                        <span class="badge badge-tone">{{ e.tone }}</span>
                        {% endif %}</td>
                    <td>
                        {% if config.derivations %}
                        <form action="/derive" method="POST"
                              style="margin:0;display:inline-flex;gap:4px;flex-wrap:wrap;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="entry_id" value="{{ e.id }}">
                            <select name="deriv_key"
                                    style="width:auto;padding:2px;font-size:.7rem;">
                                {% for dk in config.derivations.keys() %}
                                <option value="{{ dk }}">{{ dk }}</option>
                                {% endfor %}
                            </select>
                            <button type="submit" class="der-btn">+</button>
                        </form>
                        {% else %}—{% endif %}
                    </td>
                    <td>
                        <form action="/delete_entry" method="POST" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="id" value="{{ e.id }}">
                            <button type="submit"
                                style="background:none;border:none;color:var(--text-muted);
                                       cursor:pointer;padding:0;margin:0;width:auto;">
                                &times;</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="8" style="text-align:center;padding:20px;color:var(--text-muted);">
                    Lexicon is empty.</td></tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- TAB: TOOLS -->
    <div class="tab-content" id="tab-tools">

        <!-- Sound Changes -->
        <div class="panel">
            <h2 style="margin:0 0 10px 0;border:none;">Sound Change Engine</h2>
            <div class="help" style="margin-bottom:10px;">
                Ordered rules applied during generation.
            </div>
            <form method="POST" action="/add_sound_change">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="fr" style="align-items:flex-end;">
                    <div><label>From</label>
                        <input type="text" name="sc_from" placeholder="p" required></div>
                    <div><label>To</label>
                        <input type="text" name="sc_to" placeholder="b"></div>
                    <div style="flex:1;"><label>Context</label>
                        <select name="sc_context">
                            <option value="_">Everywhere</option>
                            <option value="V_V">Between vowels</option>
                            <option value="#_">Word-initial</option>
                            <option value="_#">Word-final</option>
                        </select>
                    </div>
                    <div><button type="submit" class="ico-btn"
                                 style="margin-top:22px;">+ Add</button></div>
                </div>
            </form>
            <div style="margin-top:10px;">
                {% for sc in config.sound_changes %}
                <div class="fa" style="font-size:.8rem;padding:4px 0;
                     border-bottom:1px dashed var(--brd);font-family:monospace;">
                    <span>{{ sc.from }} → {{ sc.to }} / {{ sc.context }}</span>
                    <form action="/remove_sound_change" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="idx" value="{{ loop.index0 }}">
                        <button type="submit"
                            style="background:none;color:var(--err);border:none;padding:0;
                                   margin:0;cursor:pointer;width:auto;">&times;</button>
                    </form>
                </div>
                {% else %}
                <div style="color:var(--text-muted);font-size:.8rem;padding:10px 0;">
                    No sound changes defined.</div>
                {% endfor %}
            </div>
        </div>

        <!-- IPA Map -->
        <div class="panel">
            <h2 style="margin:0 0 10px 0;border:none;">IPA Romanization Map</h2>
            <div class="help" style="margin-bottom:10px;">
                Longer graphemes matched first (e.g. "sh" before "s").</div>
            <form method="POST" action="/add_ipa">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="fr" style="align-items:flex-end;">
                    <div><label>Grapheme</label>
                        <input type="text" name="grapheme" placeholder="sh" required></div>
                    <div><label>IPA</label>
                        <input type="text" name="ipa_symbol" placeholder="ʃ" required></div>
                    <div><button type="submit" class="ico-btn"
                                 style="margin-top:22px;">+ Add</button></div>
                </div>
            </form>
            <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:5px;">
                {% for g, ipa in config.ipa_map.items() %}
                <form action="/remove_ipa" method="POST" style="margin:0;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <input type="hidden" name="grapheme" value="{{ g }}">
                    <button type="submit"
                        style="background:var(--bg-light);color:var(--text-primary);
                               border:1px solid var(--brd);padding:3px 8px;margin:0;
                               width:auto;font-size:.8rem;font-family:monospace;
                               cursor:pointer;">{{ g }}→{{ ipa }} ×</button>
                </form>
                {% else %}
                <div style="color:var(--text-muted);font-size:.8rem;">No mappings.</div>
                {% endfor %}
            </div>
        </div>

        <!-- Import -->
        <div class="panel">
            <h2 style="margin:0 0 10px 0;border:none;">Import / Restore</h2>
            <form method="POST" action="/import_json" enctype="multipart/form-data">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="file" name="json_file" accept=".json"
                       id="import-file-input"
                       style="font-size:.85rem;"
                       onchange="handleFileSelect(this)">
                <div class="help">
                    Upload a previously saved or exported JSON file to restore config and lexicon.
                </div>
                <button type="submit" id="import-btn" disabled>Import &amp; Restore</button>
            </form>
        </div>

        <!-- Saved Projects -->
        <div class="panel">
            <h2 style="margin:0 0 10px 0;border:none;">Saved Projects</h2>
            <div class="help" style="margin-bottom:10px;">
                Saved to server. Click to load or download the file.
            </div>
            {% for sv in saved_projects %}
            <div class="fa" style="font-size:.8rem;padding:6px 0;
                 border-bottom:1px dashed var(--brd);">
                <span>
                    <strong>{{ sv.name }}</strong>
                    <span style="color:var(--text-muted);">
                        {{ sv.entries }} words · {{ sv.date }}</span>
                </span>
                <div class="fr">
                    <form action="/load_project" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="filename" value="{{ sv.filename }}">
                        <button type="submit" class="ico-btn"
                                style="font-size:.7rem;">Load</button>
                    </form>
                    <a href="/download_project/{{ sv.filename }}"
                       style="text-decoration:none;">
                        <button type="button" class="ico-btn"
                                style="font-size:.7rem;">Download</button>
                    </a>
                    <form action="/delete_project" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="filename" value="{{ sv.filename }}">
                        <button type="submit"
                            style="background:none;color:var(--err);border:none;padding:0;
                                   margin:0;cursor:pointer;width:auto;">&times;</button>
                    </form>
                </div>
            </div>
            {% else %}
            <div style="color:var(--text-muted);font-size:.8rem;padding:10px 0;">
                No saved projects yet.</div>
            {% endfor %}
        </div>

        <!-- Phoneme Weights -->
        <div class="panel">
            <h2 style="margin:0 0 10px 0;border:none;">Phoneme Frequency Weights</h2>
            <div class="help" style="margin-bottom:10px;">
                Higher = more frequent (1-10). Auto-populated by corpus analysis.
            </div>
            <form method="POST" action="/update_weights">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div style="display:flex;flex-wrap:wrap;gap:8px;">
                    {% set all_p = config.vowels + config.consonants %}
                    {% for p in all_p %}
                    <div style="text-align:center;">
                        <div style="font-weight:bold;font-family:monospace;
                                    font-size:1.1rem;color:var(--text-word);">{{ p }}</div>
                        <input type="number" name="w_{{ p }}"
                               value="{{ config.phoneme_weights.get(p, 5) }}"
                               min="1" max="10"
                               style="width:50px;text-align:center;padding:3px;">
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" style="margin-top:10px;">Save Weights</button>
            </form>
        </div>
    </div>

</div>
</div>

<script>
/* ── Tab switching ── */
function switchTab(name) {
    document.querySelectorAll('.tab-content').forEach(
        function(e) { e.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(
        function(e) { e.classList.remove('active'); });
    document.getElementById('tab-' + name).classList.add('active');
    event.target.classList.add('active');
}

/* ── Lexicon search/filter ── */
function filterTable() {
    var q = document.getElementById('search-input').value.toLowerCase();
    var cf = document.getElementById('filter-cat').value;
    document.querySelectorAll('#lex-table tbody tr').forEach(function(r) {
        var w = r.getAttribute('data-word') || '';
        var m = r.getAttribute('data-meaning') || '';
        var c = r.getAttribute('data-cat') || '';
        var mt = !q || w.indexOf(q) > -1 || m.indexOf(q) > -1;
        var mc = !cf || c === cf;
        r.style.display = (mt && mc) ? '' : 'none';
    });
}

/* ── Import button: enabled only when file selected ── */
function handleFileSelect(input) {
    var btn = document.getElementById('import-btn');
    if (input.files && input.files.length > 0) {
        btn.disabled = false;
        btn.textContent = 'Import "' + input.files[0].name + '"';
    } else {
        btn.disabled = true;
        btn.textContent = 'Import & Restore';
    }
}

/* ── Night Mode ── */
function toggleTheme() {
    var html = document.documentElement;
    var current = html.getAttribute('data-theme');
    var icon = document.getElementById('theme-icon');
    var label = document.getElementById('theme-label');

    if (current === 'dark') {
        html.removeAttribute('data-theme');
        icon.textContent = '🌙';
        label.textContent = 'Night View';
        localStorage.setItem('conlang-theme', 'light');
    } else {
        html.setAttribute('data-theme', 'dark');
        icon.textContent = '☀️';
        label.textContent = 'Day View';
        localStorage.setItem('conlang-theme', 'dark');
    }
}

/* Persist theme across page loads */
(function() {
    var saved = localStorage.getItem('conlang-theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        var icon = document.getElementById('theme-icon');
        var label = document.getElementById('theme-label');
        if (icon) icon.textContent = '☀️';
        if (label) label.textContent = 'Day View';
    }
})();
</script>

</body>
</html>
"""


# ──────────────────────────────────────────────
# SESSION HELPERS
# ──────────────────────────────────────────────

SAVE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'saved_projects'
)


def ensure_save_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def init_session():
    if 'config' not in session:
        session['config'] = engine.get_defaults()
    cfg = session['config']
    d = engine.defaults
    for key in d:
        if key not in cfg:
            cfg[key] = copy.deepcopy(d[key])
    if 'dictionary' not in session:
        session['dictionary'] = []
    if 'batch' not in session:
        session['batch'] = []
    if 'corpus' not in session:
        session['corpus'] = ''


def compute_stats(dictionary):
    classes = set()
    categories = set()
    derived = 0
    for e in dictionary:
        cl = e.get('class', '')
        if cl:
            classes.add(cl)
        categories.add(e.get('category', 'General'))
        if e.get('derived_from'):
            derived += 1
    return {
        "classes": len(classes),
        "categories": len(categories),
        "derived": derived,
    }


def list_saved_projects():
    ensure_save_dir()
    projects = []
    for fn in sorted(os.listdir(SAVE_DIR), reverse=True):
        if fn.endswith('.json'):
            fp = os.path.join(SAVE_DIR, fn)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                meta = data.get('meta', {})
                projects.append({
                    "filename": fn,
                    "name": meta.get('project_name', fn),
                    "date": meta.get('saved_at', '?'),
                    "entries": meta.get('entry_count', 0),
                })
            except (json.JSONDecodeError, IOError):
                pass
    return projects


def render_page(flash_msg=None, flash_type=None):
    init_session()
    return render_template_string(
        HTML_TEMPLATE,
        config=session['config'],
        batch=session['batch'],
        dictionary=session['dictionary'],
        stats=compute_stats(session['dictionary']),
        session_corpus=session.get('corpus', ''),
        saved_projects=list_saved_projects(),
        flash_msg=flash_msg,
        flash_type=flash_type,
    )


# ──────────────────────────────────────────────
# ROUTES: Index + Config
# ──────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    return render_page()


@app.route('/update_config', methods=['POST'])
def update_config():
    init_session()
    cfg = session['config']

    corpus = request.form.get('corpus', '').strip()
    session['corpus'] = corpus

    if corpus:
        v, c, w = engine.analyze_corpus(corpus)
        if v:
            cfg['vowels'] = v
        if c:
            cfg['consonants'] = c
        if w:
            cfg['phoneme_weights'] = w
    else:
        cfg['vowels'] = request.form.get('vowels', '') or cfg['vowels']
        cfg['consonants'] = (
            request.form.get('consonants', '') or cfg['consonants']
        )

    tones_raw = request.form.get('tones', '')
    cfg['tones'] = [t.strip() for t in tones_raw.split(',') if t.strip()]

    fc_raw = request.form.get('forbidden_clusters', '')
    cfg['forbidden_clusters'] = [
        f.strip().lower() for f in fc_raw.split(',') if f.strip()
    ]

    struct_raw = request.form.get('structures', '')
    parsed = [s.strip().upper() for s in struct_raw.split(',') if s.strip()]
    cfg['structures'] = parsed if parsed else cfg['structures']

    try:
        min_s = max(1, int(request.form.get('min_syl', 2)))
        max_s = max(1, int(request.form.get('max_syl', 3)))
        if max_s < min_s:
            max_s = min_s
        cfg['min_syl'] = min_s
        cfg['max_syl'] = max_s
    except (ValueError, TypeError):
        pass

    cfg['vowel_harmony'] = bool(request.form.get('vowel_harmony'))
    front = request.form.get('harmony_front', '').strip()
    back = request.form.get('harmony_back', '').strip()
    if front or back:
        cfg['harmony_groups'] = {
            "front": front or cfg['harmony_groups']['front'],
            "back": back or cfg['harmony_groups']['back'],
        }

    session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Morphology (fully deletable)
# ──────────────────────────────────────────────

@app.route('/add_class', methods=['POST'])
def add_class():
    init_session()
    name = request.form.get('c_name', '').strip()
    if not name:
        return redirect(url_for('index'))

    mode = request.form.get('c_mode', 'simple')
    if mode == 'regex':
        pattern = request.form.get('c_pattern', '').strip()
        replacement = request.form.get('c_replacement', '').strip()
        try:
            re.compile(pattern)
        except re.error:
            return render_page(
                f'Invalid regex pattern: "{pattern}"',
                flash_type="error",
            )
        session['config']['morphology'][name] = {
            "mode": "regex",
            "pre": "", "suf": "",
            "pattern": pattern,
            "replacement": replacement,
        }
    else:
        session['config']['morphology'][name] = {
            "mode": "simple",
            "pre": request.form.get('c_pre', '') or '',
            "suf": request.form.get('c_suf', '') or '',
            "pattern": "", "replacement": "",
        }

    session.modified = True
    return redirect(url_for('index'))


@app.route('/remove_class', methods=['POST'])
def remove_class():
    init_session()
    name = request.form.get('name')
    morph = session['config']['morphology']
    if name and name in morph:
        del morph[name]
        session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Derivation (with regex support)
# ──────────────────────────────────────────────

@app.route('/add_derivation', methods=['POST'])
def add_derivation():
    init_session()
    name = request.form.get('d_name', '').strip()
    if not name:
        return redirect(url_for('index'))

    mode = request.form.get('d_mode', 'simple')
    if mode == 'regex':
        pattern = request.form.get('d_pattern', '').strip()
        replacement = request.form.get('d_replacement', '').strip()
        try:
            re.compile(pattern)
        except re.error:
            return render_page(
                f'Invalid regex pattern: "{pattern}"',
                flash_type="error",
            )
        session['config']['derivations'][name] = {
            "mode": "regex",
            "pre": "", "suf": "",
            "pattern": pattern,
            "replacement": replacement,
        }
    else:
        session['config']['derivations'][name] = {
            "mode": "simple",
            "pre": request.form.get('d_pre', '') or '',
            "suf": request.form.get('d_suf', '') or '',
            "pattern": "", "replacement": "",
        }

    session.modified = True
    return redirect(url_for('index'))


@app.route('/remove_derivation', methods=['POST'])
def remove_derivation():
    init_session()
    name = request.form.get('name')
    derivs = session['config']['derivations']
    if name and name in derivs:
        del derivs[name]
        session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Generation & Approval
# ──────────────────────────────────────────────

@app.route('/generate', methods=['POST'])
def generate():
    init_session()
    meaning = request.form.get('meaning', '').strip()
    class_key = request.form.get('class_key', '__none__')
    category = request.form.get('category', 'General')

    if not meaning:
        return render_page("Enter a target concept.", flash_type="error")

    try:
        count = min(20, max(1, int(request.form.get('count', 8))))
    except (ValueError, TypeError):
        count = 8

    batch = engine.generate_batch(
        session['config'], meaning, class_key, count, category
    )

    if not batch:
        return render_page(
            "Generation failed — check vowels, consonants, "
            "and syllable structures.",
            flash_type="error",
        )

    # Similarity warnings
    existing = session.get('dictionary', [])
    for cand in batch:
        sim = engine.find_similar(cand['word'], existing, threshold=2)
        cand['similar'] = [
            f"{s['word']} ({s['meaning']})" for s in sim
        ]

    session['batch'] = batch
    session.modified = True
    return redirect(url_for('index'))


@app.route('/approve_one', methods=['POST'])
def approve_one():
    init_session()
    c_id = request.form.get('id')
    batch = session.get('batch', [])
    existing = {e['word'] for e in session.get('dictionary', [])}

    cand = next((i for i in batch if i['id'] == c_id), None)
    if cand:
        if cand['word'] in existing:
            return render_page(
                f'"{cand["word"]}" already exists.',
                flash_type="warning",
            )
        entry = cand.copy()
        entry.pop('similar', None)
        entry['id'] = str(uuid.uuid4())
        session['dictionary'].insert(0, entry)
        session['batch'] = [i for i in batch if i['id'] != c_id]
        session.modified = True

    return redirect(url_for('index'))


@app.route('/approve_all', methods=['POST'])
def approve_all():
    init_session()
    batch = session.get('batch', [])
    existing = {e['word'] for e in session.get('dictionary', [])}
    added = skipped = 0

    for cand in batch:
        if cand['word'] not in existing:
            entry = cand.copy()
            entry.pop('similar', None)
            entry['id'] = str(uuid.uuid4())
            session['dictionary'].insert(0, entry)
            existing.add(entry['word'])
            added += 1
        else:
            skipped += 1

    session['batch'] = []
    session.modified = True

    msg = f"{added} entries approved."
    if skipped:
        msg += f" {skipped} duplicates skipped."
    return render_page(
        msg, flash_type="ok" if not skipped else "warning"
    )


@app.route('/clear_batch', methods=['POST'])
def clear_batch():
    session['batch'] = []
    session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Derivation from Lexicon
# ──────────────────────────────────────────────

@app.route('/derive', methods=['POST'])
def derive():
    init_session()
    entry_id = request.form.get('entry_id')
    deriv_key = request.form.get('deriv_key')

    source = next(
        (e for e in session['dictionary'] if e['id'] == entry_id),
        None,
    )
    if not source:
        return render_page("Source word not found.", flash_type="error")

    derived = engine.derive_word(source, deriv_key, session['config'])
    if not derived:
        return render_page(
            f'Derivation "{deriv_key}" not defined.',
            flash_type="error",
        )

    existing = {e['word'] for e in session['dictionary']}
    if derived['word'] in existing:
        return render_page(
            f'"{derived["word"]}" already exists.',
            flash_type="warning",
        )

    derived['ipa'] = engine.to_ipa(
        derived['word'], session['config'].get('ipa_map', {})
    )
    derived['tone'] = source.get('tone', '')

    session['dictionary'].insert(0, derived)
    session.modified = True
    return render_page(
        f'Derived "{derived["word"]}" from '
        f'"{source["word"]}" ({deriv_key}).',
        flash_type="ok",
    )


# ──────────────────────────────────────────────
# ROUTES: Dictionary Management
# ──────────────────────────────────────────────

@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    init_session()
    e_id = request.form.get('id')
    session['dictionary'] = [
        i for i in session['dictionary'] if i['id'] != e_id
    ]
    session.modified = True
    return redirect(url_for('index'))


@app.route('/purge_dict', methods=['POST'])
def purge_dict():
    session['dictionary'] = []
    session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Sound Changes
# ──────────────────────────────────────────────

@app.route('/add_sound_change', methods=['POST'])
def add_sound_change():
    init_session()
    sc_from = request.form.get('sc_from', '').strip()
    sc_to = request.form.get('sc_to', '').strip()
    sc_context = request.form.get('sc_context', '_').strip()

    if sc_from:
        session['config']['sound_changes'].append({
            "from": sc_from,
            "to": sc_to,
            "context": sc_context,
        })
        session.modified = True
    return redirect(url_for('index'))


@app.route('/remove_sound_change', methods=['POST'])
def remove_sound_change():
    init_session()
    try:
        idx = int(request.form.get('idx', -1))
        changes = session['config']['sound_changes']
        if 0 <= idx < len(changes):
            changes.pop(idx)
            session.modified = True
    except (ValueError, TypeError):
        pass
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: IPA Mapping
# ──────────────────────────────────────────────

@app.route('/add_ipa', methods=['POST'])
def add_ipa():
    init_session()
    grapheme = request.form.get('grapheme', '').strip().lower()
    ipa_symbol = request.form.get('ipa_symbol', '').strip()
    if grapheme and ipa_symbol:
        session['config']['ipa_map'][grapheme] = ipa_symbol
        session.modified = True
    return redirect(url_for('index'))


@app.route('/remove_ipa', methods=['POST'])
def remove_ipa():
    init_session()
    grapheme = request.form.get('grapheme', '').strip().lower()
    ipa_map = session['config'].get('ipa_map', {})
    if grapheme in ipa_map:
        del ipa_map[grapheme]
        session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Phoneme Weights
# ──────────────────────────────────────────────

@app.route('/update_weights', methods=['POST'])
def update_weights():
    init_session()
    cfg = session['config']
    all_phonemes = (cfg.get('vowels', '') or '') + (
        cfg.get('consonants', '') or ''
    )
    weights = {}
    for p in all_phonemes:
        raw = request.form.get(f'w_{p}', '5')
        try:
            w = min(10, max(1, int(raw)))
        except (ValueError, TypeError):
            w = 5
        weights[p] = w

    cfg['phoneme_weights'] = weights
    session.modified = True
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# ROUTES: Export
# ──────────────────────────────────────────────

@app.route('/export')
def export():
    init_session()
    data = {
        "meta": {
            "generated_by": "Conlang_Generator_V2",
            "timestamp": str(datetime.datetime.now()),
            "entry_count": len(session.get('dictionary', [])),
        },
        "config": session.get('config'),
        "lexicon": session.get('dictionary'),
    }
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={
            "Content-Disposition":
                "attachment; filename=conlang_lexicon.json"
        },
    )


# ──────────────────────────────────────────────
# ROUTES: Save / Load / Download / Delete Projects
# ──────────────────────────────────────────────

@app.route('/save_project', methods=['POST'])
def save_project():
    init_session()
    ensure_save_dir()

    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    display_date = now.strftime("%Y-%m-%d %H:%M")

    dict_entries = session.get('dictionary', [])
    if dict_entries:
        sample_meanings = []
        seen = set()
        for e in dict_entries:
            m = e.get('meaning', '').strip()
            if m and m not in seen:
                sample_meanings.append(m)
                seen.add(m)
            if len(sample_meanings) >= 3:
                break
        project_label = ", ".join(sample_meanings)
        if len(dict_entries) > 3:
            project_label += f" (+{len(dict_entries) - 3} more)"
    else:
        project_label = "Empty project"

    filename = f"conlang_{timestamp_str}.json"
    filepath = os.path.join(SAVE_DIR, filename)

    data = {
        "meta": {
            "generated_by": "Conlang_Generator_V2",
            "project_name": project_label,
            "saved_at": display_date,
            "entry_count": len(dict_entries),
        },
        "config": session.get('config'),
        "lexicon": dict_entries,
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        return render_page(
            f"Failed to save: {e}", flash_type="error"
        )

    return render_page(
        f'Project saved: "{project_label}" '
        f'({len(dict_entries)} entries).',
        flash_type="ok",
    )


@app.route('/load_project', methods=['POST'])
def load_project():
    init_session()
    filename = request.form.get('filename', '').strip()

    if not filename or '..' in filename or '/' in filename:
        return render_page("Invalid filename.", flash_type="error")

    filepath = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(filepath):
        return render_page("File not found.", flash_type="error")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return render_page(
            f"Failed to load: {e}", flash_type="error"
        )

    restored = _restore_from_data(data)

    if restored:
        return render_page(
            f"Loaded: {', '.join(restored)}.",
            flash_type="ok",
        )
    return render_page(
        "No recognizable data found.", flash_type="warning"
    )


@app.route('/download_project/<filename>')
def download_project(filename):
    if not filename or '..' in filename or '/' in filename:
        return redirect(url_for('index'))

    filepath = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(filepath):
        return redirect(url_for('index'))

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError:
        return redirect(url_for('index'))

    return Response(
        content,
        mimetype="application/json",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        },
    )


@app.route('/delete_project', methods=['POST'])
def delete_project():
    init_session()
    filename = request.form.get('filename', '').strip()

    if not filename or '..' in filename or '/' in filename:
        return render_page("Invalid filename.", flash_type="error")

    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except IOError as e:
            return render_page(
                f"Failed to delete: {e}", flash_type="error"
            )

    return render_page("Project deleted.", flash_type="ok")


# ──────────────────────────────────────────────
# ROUTES: Import from Uploaded File
# ──────────────────────────────────────────────

@app.route('/import_json', methods=['POST'])
def import_json():
    init_session()

    uploaded = request.files.get('json_file')
    if not uploaded or not uploaded.filename:
        return render_page("No file selected.", flash_type="error")

    if not uploaded.filename.lower().endswith('.json'):
        return render_page(
            "Only .json files accepted.", flash_type="error"
        )

    try:
        raw = uploaded.read().decode('utf-8')
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return render_page(
            f"Invalid JSON: {e}", flash_type="error"
        )

    if not isinstance(data, dict):
        return render_page(
            "Expected a JSON object.", flash_type="error"
        )

    restored = _restore_from_data(data)

    if restored:
        return render_page(
            f"Imported: {', '.join(restored)}.",
            flash_type="ok",
        )
    return render_page(
        "Valid JSON but no recognizable data.",
        flash_type="warning",
    )


# ──────────────────────────────────────────────
# SHARED: Restore logic (used by load + import)
# ──────────────────────────────────────────────

def _restore_from_data(data):
    """
    Restores config and lexicon from a parsed JSON dict.
    Returns list of restored component names.
    """
    restored = []

    imported_config = data.get('config')
    if imported_config and isinstance(imported_config, dict):
        merged = engine.get_defaults()
        for key, value in imported_config.items():
            if key in merged:
                merged[key] = value
        session['config'] = merged
        restored.append("configuration")

    imported_lexicon = data.get('lexicon')
    if imported_lexicon and isinstance(imported_lexicon, list):
        valid = []
        for entry in imported_lexicon:
            if isinstance(entry, dict) and 'word' in entry:
                entry.setdefault('id', str(uuid.uuid4()))
                entry.setdefault('root', entry['word'])
                entry.setdefault('class', '')
                entry.setdefault('meaning', '')
                entry.setdefault('category', 'General')
                entry.setdefault('derived_from', '')
                entry.setdefault('tone', '')
                entry.setdefault('ipa', '')
                entry.setdefault(
                    'timestamp',
                    datetime.datetime.now().strftime("%H:%M:%S"),
                )
                valid.append(entry)
        session['dictionary'] = valid
        restored.append(f"lexicon ({len(valid)} entries)")

    session['batch'] = []
    session.modified = True
    return restored


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == '__main__':
    ensure_save_dir()
    app.run(debug=True, port=5000)
