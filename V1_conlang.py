from flask import Flask, render_template_string, request, session, redirect, url_for, Response
import random
import re
import json
import uuid
import datetime

# Tèret's Seal of Approval
app = Flask(__name__)
app.secret_key = "GRESOIDIA_FINAL_STANDARD_ORDER_LAW_999"

# ------------------------------------------------------------------
# THE LOGIC CORE: The Standardized Linguistic Engine
# ------------------------------------------------------------------

class LinguisticStandardEngine:
    def __init__(self):
        # The Baseline Configuration (Default Laws)
        self.defaults = {
            "vowels": "aeiou",
            "consonants": "ptkmnls",
            "structures": ["CV", "CVC", "VC"], # Allowable syllable shapes
            "tones": [],
            "min_syl": 2,
            "max_syl": 3,
            "morphology": { # Genders/Classes
                "Neutral": {"pre": "", "suf": ""},
                "Masculine": {"pre": "", "suf": "os"},
                "Feminine": {"pre": "", "suf": "a"},
                "Plural": {"pre": "ge", "suf": "i"}
            }
        }

    def analyze_corpus(self, text):
        """
        Extracts legal phonemes from raw text.
        Optimization: Sets are sorted for consistent indexing.
        """
        if not text: return None, None
        clean = re.sub(r'[^a-zA-Z]', '', text.lower())
        v = sorted(list(set([c for c in clean if c in "aeiouy"])))
        c = sorted(list(set([c for c in clean if c not in "aeiouy"])))
        return "".join(v), "".join(c)

    def validate_euphony(self, word):
        """
        Tèret's Law: Words must be pronounceable.
        Rejects clusters of 3+ consonants or vowels.
        """
        if re.search(r'[aeiouy]{3,}', word): return False
        if re.search(r'[^aeiouy]{3,}', word): return False
        return True

    def generate_batch(self, config, meaning, class_key, count=8):
        """
        Generates a pool of candidates based on strict variable rules.
        """
        candidates = []
        
        # Load Laws
        vowels = list(config.get('vowels', self.defaults['vowels']))
        consonants = list(config.get('consonants', self.defaults['consonants']))
        structures = config.get('structures', self.defaults['structures'])
        tones = config.get('tones', [])
        
        # Morphology (Gender)
        classes = config.get('morphology', self.defaults['morphology'])
        rule = classes.get(class_key, {"pre":"", "suf":""})

        min_s = int(config.get('min_syl', 2))
        max_s = int(config.get('max_syl', 3))

        attempts = 0
        while len(candidates) < count and attempts < (count * 10):
            attempts += 1
            word_root = ""
            
            # Variable Syllable Loop
            syl_count = random.randint(min_s, max_s)
            
            for _ in range(syl_count):
                struct = random.choice(structures)
                for char_type in struct:
                    if char_type == 'C':
                        word_root += random.choice(consonants)
                    elif char_type == 'V':
                        word_root += random.choice(vowels)
            
            # Apply Tonal Layer (If defined)
            if tones:
                # Standard: Tone applied to the end of the root
                word_root += random.choice(tones)

            # Euphony Check (Reject chaos)
            if not self.validate_euphony(word_root):
                continue

            # Apply Morphology
            full_word = f"{rule['pre']}{word_root}{rule['suf']}"
            
            candidates.append({
                "id": str(uuid.uuid4()),
                "word": full_word,
                "root": word_root,
                "class": class_key,
                "meaning": meaning,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            })
            
        return candidates

engine = LinguisticStandardEngine()

# ------------------------------------------------------------------
# THE INTERFACE: Professional, Clean, Optimized
# ------------------------------------------------------------------

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gresoidia: Linguistic Standard v3.0</title>
    <style>
        :root {
            --primary: #2c3e50; /* Official Blue */
            --secondary: #34495e;
            --accent: #2980b9;
            --light: #ecf0f1;
            --border: #bdc3c7;
            --success: #27ae60;
            --danger: #c0392b;
        }
        
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f7;
            color: #333;
            margin: 0; padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header */
        header {
            background: var(--primary);
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 4px solid var(--accent);
        }
        .brand { font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 1.2rem; }
        .status { font-size: 0.8rem; opacity: 0.8; }
        
        /* Main Grid */
        .layout {
            display: grid;
            grid-template-columns: 350px 1fr;
            flex: 1;
            overflow: hidden;
        }
        
        /* Sidebar (Controls) */
        .sidebar {
            background: white;
            border-right: 1px solid var(--border);
            padding: 20px;
            overflow-y: auto;
        }
        
        h2 { font-size: 0.9rem; color: var(--secondary); text-transform: uppercase; border-bottom: 2px solid var(--light); padding-bottom: 5px; margin-top: 25px; }
        h2:first-child { margin-top: 0; }
        
        label { display: block; font-size: 0.8rem; font-weight: 600; margin-top: 10px; color: #555; }
        
        input[type="text"], input[type="number"], textarea, select {
            width: 100%; padding: 8px; margin-top: 4px; border: 1px solid var(--border);
            border-radius: 3px; font-family: monospace; box-sizing: border-box;
        }
        input:focus { border-color: var(--accent); outline: none; }
        
        /* Buttons */
        button {
            width: 100%; padding: 10px; border: none; background: var(--secondary);
            color: white; font-weight: 600; cursor: pointer; border-radius: 3px;
            margin-top: 15px; text-transform: uppercase; font-size: 0.8rem;
            transition: 0.2s;
        }
        button:hover { background: var(--accent); }
        button.action-btn { background: var(--success); padding: 15px; font-size: 0.9rem; }
        button.danger-btn { background: var(--danger); width: auto; padding: 5px 10px; margin: 0; font-size: 0.7rem; }
        button.icon-btn { background: transparent; color: #999; border: 1px solid #ccc; width: auto; margin:0; padding: 5px 10px; color: #333;}
        
        /* Main Workspace */
        .workspace {
            padding: 30px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        /* Panels */
        .panel {
            background: white;
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Batch Grid */
        .batch-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .candidate-card {
            background: white;
            border: 1px solid var(--border);
            padding: 15px;
            text-align: center;
            border-radius: 4px;
            transition: 0.2s;
            position: relative;
        }
        .candidate-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        
        .word-display { font-size: 1.3rem; font-weight: bold; color: var(--primary); margin-bottom: 5px; }
        .word-meta { font-size: 0.75rem; color: #7f8c8d; }
        
        /* Data Table */
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
        th { text-align: left; background: var(--light); padding: 10px; border-bottom: 2px solid var(--border); }
        td { padding: 10px; border-bottom: 1px solid #eee; }
        
        .badge { background: var(--light); padding: 2px 6px; border-radius: 3px; font-size: 0.75rem; border: 1px solid #ccc; }
        
        /* Flex Utils */
        .flex-row { display: flex; gap: 10px; }
        .flex-apart { display: flex; justify-content: space-between; align-items: center; }

    </style>
</head>
<body>

<header>
    <div class="brand">Gresoidia Tower <span style="font-weight:300; opacity:0.7;">| Dept. of Order</span></div>
    <div class="status">System Status: OPTIMAL</div>
</header>

<div class="layout">
    
    <!-- LEFT PANEL: RULES & LAWS -->
    <div class="sidebar">
        <form method="POST" action="/update_config">
            <h2>1. Phonemic Inventory</h2>
            <button type="button" onclick="document.getElementById('corpus_input').style.display='block'" class="icon-btn" style="width:100%; margin-bottom:10px;">Analyze Source Text</button>
            <div id="corpus_input" style="display:none; margin-bottom: 10px;">
                <textarea name="corpus" rows="3" placeholder="Paste source material here..."></textarea>
            </div>
            
            <label>Vowels (V)</label>
            <input type="text" name="vowels" value="{{ config.vowels }}">
            
            <label>Consonants (C)</label>
            <input type="text" name="consonants" value="{{ config.consonants }}">
            
            <label>Tones (Optional)</label>
            <input type="text" name="tones" value="{{ config.tones|join(',') }}" placeholder="e.g. high, low">
            
            <h2>2. Structural Logic</h2>
            <label>Permitted Syllables</label>
            <input type="text" name="structures" value="{{ config.structures|join(',') }}" placeholder="e.g. CV, CVC">
            
            <label>Syllable Count Range</label>
            <div class="flex-row">
                <input type="number" name="min_syl" value="{{ config.min_syl }}" min="1" max="10">
                <input type="number" name="max_syl" value="{{ config.max_syl }}" min="1" max="10">
            </div>

            <button type="submit">Update Standards</button>
        </form>

        <h2>3. Morphological Classes</h2>
        <form method="POST" action="/add_class">
            <input type="text" name="c_name" placeholder="Class Name (e.g. Divine)" required>
            <div class="flex-row">
                <input type="text" name="c_pre" placeholder="Prefix">
                <input type="text" name="c_suf" placeholder="Suffix">
            </div>
            <button type="submit" class="icon-btn" style="width:100%; margin-top:5px; background: #eee;">+ Add Class definition</button>
        </form>

        <div style="margin-top: 15px;">
            {% for name, rules in config.morphology.items() %}
            <div class="flex-apart" style="font-size: 0.8rem; padding: 5px 0; border-bottom: 1px dashed #eee;">
                <span><strong>{{ name }}</strong> <span style="color:#999;">({{ rules.pre }}...{{ rules.suf }})</span></span>
                <form action="/remove_class" method="POST" style="margin:0;">
                    <input type="hidden" name="name" value="{{ name }}">
                    <button type="submit" style="background:none; color:red; border:none; padding:0; margin:0; cursor:pointer;">&times;</button>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- RIGHT PANEL: EXECUTION -->
    <div class="workspace">
        
        <!-- GENERATION UNIT -->
        <div class="panel">
            <div class="flex-apart">
                <h2 style="margin:0; border:none;">Generation Protocol</h2>
                <form action="/clear_batch" method="POST" style="margin:0;">
                    <button type="submit" class="icon-btn">Clear Workspace</button>
                </form>
            </div>
            
            <form method="POST" action="/generate">
                <div class="flex-row" style="align-items: flex-end;">
                    <div style="flex: 2;">
                        <label>Target Concept (English)</label>
                        <input type="text" name="meaning" placeholder="e.g. Order" required>
                    </div>
                    <div style="flex: 1;">
                        <label>Morphological Class</label>
                        <select name="class_key">
                            {% for k in config.morphology.keys() %}
                            <option value="{{ k }}">{{ k }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div style="flex: 1;">
                        <label>Batch Size</label>
                        <input type="number" name="count" value="8" min="1" max="20">
                    </div>
                </div>
                <button type="submit" class="action-btn">Initialize Generation Sequence</button>
            </form>

            {% if batch %}
            <div style="margin-top: 20px; border-top: 2px solid #eee; padding-top: 15px;">
                <div class="flex-apart">
                    <span style="font-size:0.9rem; font-weight:bold; color: var(--secondary);">Candidates for: "{{ batch[0].meaning }}"</span>
                    <form action="/approve_all" method="POST" style="margin:0;">
                        <button type="submit" class="icon-btn" style="color: var(--success); border-color: var(--success);">Approve All</button>
                    </form>
                </div>
                
                <div class="batch-container">
                    {% for item in batch %}
                    <form action="/approve_one" method="POST">
                        <input type="hidden" name="id" value="{{ item.id }}">
                        <button type="submit" class="candidate-card" style="width:100%; margin:0; cursor:pointer;">
                            <div class="word-display">{{ item.word }}</div>
                            <div class="word-meta">{{ item.class }} | Root: {{ item.root }}</div>
                            <div style="margin-top:8px; font-size:0.7rem; color: var(--success); font-weight:bold;">[ APPROVE ]</div>
                        </button>
                    </form>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>

        <!-- DATABASE UNIT -->
        <div class="panel">
            <div class="flex-apart">
                <h2 style="margin:0; border:none;">Approved Lexicon ({{ dictionary|length }} entries)</h2>
                <div class="flex-row">
                    <a href="/export" style="text-decoration:none;"><button class="icon-btn">Export JSON</button></a>
                    <form action="/purge_dict" method="POST" style="margin:0;">
                        <button type="submit" class="danger-btn">Purge Database</button>
                    </form>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th width="25%">Concept</th>
                        <th width="15%">Class</th>
                        <th width="35%">Standardized Form</th>
                        <th width="25%">Timestamp</th>
                        <th width="5%"></th>
                    </tr>
                </thead>
                <tbody>
                    {% for entry in dictionary %}
                    <tr>
                        <td>{{ entry.meaning }}</td>
                        <td><span class="badge">{{ entry.class }}</span></td>
                        <td style="font-weight:bold; color: var(--primary);">{{ entry.word }}</td>
                        <td style="font-size:0.8rem; color:#999;">{{ entry.timestamp }}</td>
                        <td>
                            <form action="/delete_entry" method="POST" style="margin:0;">
                                <input type="hidden" name="id" value="{{ entry.id }}">
                                <button type="submit" style="background:none; border:none; color:#ccc; cursor:pointer; padding:0; margin:0;">&times;</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" style="text-align:center; padding:20px; color:#999;">Database is empty. Awaiting input.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

    </div>
</div>

</body>
</html>
"""

# ------------------------------------------------------------------
# THE ROUTING SYSTEM: Stateless & Efficient
# ------------------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    # Initialize Session State
    if 'config' not in session: session['config'] = engine.defaults.copy()
    if 'dictionary' not in session: session['dictionary'] = []
    if 'batch' not in session: session['batch'] = []
    
    return render_template_string(HTML_TEMPLATE, 
                                  config=session['config'], 
                                  batch=session['batch'],
                                  dictionary=session['dictionary'])

@app.route('/update_config', methods=['POST'])
def update_config():
    cfg = session['config']
    
    # Logic: Analyze Corpus or Manual Input
    corpus = request.form.get('corpus')
    if corpus and corpus.strip():
        v, c = engine.analyze_corpus(corpus)
        if v: cfg['vowels'] = v
        if c: cfg['consonants'] = c
    else:
        cfg['vowels'] = request.form.get('vowels')
        cfg['consonants'] = request.form.get('consonants')
    
    # List processing
    tones_raw = request.form.get('tones')
    cfg['tones'] = [t.strip() for t in tones_raw.split(',') if t.strip()]
    
    struct_raw = request.form.get('structures')
    cfg['structures'] = [s.strip() for s in struct_raw.split(',') if s.strip()]
    
    # Integers
    cfg['min_syl'] = int(request.form.get('min_syl', 2))
    cfg['max_syl'] = int(request.form.get('max_syl', 3))
    
    session.modified = True
    return redirect(url_for('index'))

@app.route('/add_class', methods=['POST'])
def add_class():
    name = request.form.get('c_name')
    if name:
        session['config']['morphology'][name] = {
            "pre": request.form.get('c_pre'),
            "suf": request.form.get('c_suf')
        }
        session.modified = True
    return redirect(url_for('index'))

@app.route('/remove_class', methods=['POST'])
def remove_class():
    name = request.form.get('name')
    if name in session['config']['morphology']:
        del session['config']['morphology'][name]
        session.modified = True
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    meaning = request.form.get('meaning')
    class_key = request.form.get('class_key')
    count = int(request.form.get('count', 8))
    
    # Execute Engine
    batch = engine.generate_batch(session['config'], meaning, class_key, count)
    session['batch'] = batch
    
    return redirect(url_for('index'))

@app.route('/approve_one', methods=['POST'])
def approve_one():
    c_id = request.form.get('id')
    batch = session.get('batch', [])
    
    # Find candidate
    cand = next((item for item in batch if item['id'] == c_id), None)
    
    if cand:
        # Move to Dictionary
        entry = cand.copy()
        entry['id'] = str(uuid.uuid4()) # New ID for storage
        session['dictionary'].insert(0, entry)
        session.modified = True
        
        # Tèret's Optimization: Do not clear batch immediately, allow multiple selections.
        # But remove the approved one from the batch to prevent duplicates? 
        # No, just leave it. The user may want variations.
        
    return redirect(url_for('index'))

@app.route('/approve_all', methods=['POST'])
def approve_all():
    batch = session.get('batch', [])
    for cand in batch:
        entry = cand.copy()
        entry['id'] = str(uuid.uuid4())
        session['dictionary'].insert(0, entry)
    
    session['batch'] = [] # Clear batch after total approval
    session.modified = True
    return redirect(url_for('index'))

@app.route('/clear_batch', methods=['POST'])
def clear_batch():
    session['batch'] = []
    return redirect(url_for('index'))

@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    e_id = request.form.get('id')
    session['dictionary'] = [i for i in session['dictionary'] if i['id'] != e_id]
    session.modified = True
    return redirect(url_for('index'))

@app.route('/purge_dict', methods=['POST'])
def purge_dict():
    session['dictionary'] = []
    return redirect(url_for('index'))

@app.route('/export')
def export():
    data = {
        "meta": {"generated_by": "Gresoidia_ULS_v3", "timestamp": str(datetime.datetime.now())},
        "config": session.get('config'),
        "lexicon": session.get('dictionary')
    }
    return Response(json.dumps(data, indent=2), mimetype="application/json", 
                    headers={"Content-disposition":"attachment; filename=gresoidia_standard_lexicon.json"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)