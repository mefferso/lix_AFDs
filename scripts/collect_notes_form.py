from __future__ import annotations

from pathlib import Path


def collect_notes_form(outdir: Path, config: dict) -> None:
    html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AFD Notes Form</title>
<style>
body{font-family:Arial,sans-serif;max-width:1050px;margin:24px auto;padding:0 16px;line-height:1.35;background:#f7f7f7;color:#222}
h1{margin-bottom:0}.hint{color:#555}.card{background:white;border:1px solid #ddd;border-radius:10px;padding:16px;margin:14px 0}label{font-weight:700;display:block;margin-top:12px}textarea,input,select{width:100%;box-sizing:border-box;margin-top:5px;padding:8px;border:1px solid #bbb;border-radius:6px;font:inherit}textarea{min-height:70px}button{padding:10px 14px;border:0;border-radius:8px;cursor:pointer;margin:8px 8px 8px 0;font-weight:700}.primary{background:#222;color:white}.secondary{background:#ddd}#output{min-height:360px;font-family:Consolas,monospace;white-space:pre-wrap}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:800px){.row{grid-template-columns:1fr}}</style>
</head>
<body>
<h1>AFD Notes Form</h1>
<p class="hint">Answer only what matters. Blank fields are ignored. Click Generate Notes, then copy/paste the output into ChatGPT with <code>ai_context.md</code>.</p>
<div class="card">
<h2>Quick setup</h2>
<label>Main forecast problem</label><textarea id="mainProblem"></textarea>
<label>Biggest uncertainty</label><textarea id="uncertainty"></textarea>
<label>What changed from the previous AFD?</label><textarea id="changed"></textarea>
</div>
<div class="card">
<h2>Model guidance notes</h2>
<div class="row"><div><label>Short-term model trend</label><textarea id="shortModel"></textarea></div><div><label>Ensemble/probability signal</label><textarea id="ensemble"></textarea></div></div>
<div class="row"><div><label>Temperature / heat / PoP notes</label><textarea id="heatPop"></textarea></div><div><label>Rain / QPF notes</label><textarea id="rain"></textarea></div></div>
<label>Confidence or model disagreement</label><textarea id="modelConfidence"></textarea>
</div>
<div class="card">
<h2>Current trend notes</h2>
<div class="row"><div><label>Where activity is now</label><textarea id="nowLocation"></textarea></div><div><label>Movement / timing</label><textarea id="movement"></textarea></div></div>
<div class="row"><div><label>Cloud / heating trend</label><textarea id="clouds"></textarea></div><div><label>Boundaries / focus areas</label><textarea id="boundaries"></textarea></div></div>
<label>Next 1 to 3 hours</label><textarea id="nextHours"></textarea>
</div>
<div class="card">
<h2>Impacts</h2>
<div class="row"><div><label>Public / DSS impacts</label><textarea id="publicImpacts"></textarea></div><div><label>Aviation impacts</label><textarea id="aviation"></textarea></div></div>
<div class="row"><div><label>Marine impacts</label><textarea id="marine"></textarea></div><div><label>Words or ideas to avoid</label><textarea id="avoid"></textarea></div></div>
</div>
<div class="card">
<button class="primary" onclick="generateNotes()">Generate Notes</button>
<button class="secondary" onclick="copyNotes()">Copy Notes</button>
<button class="secondary" onclick="downloadNotes()">Download notes.md</button>
<button class="secondary" onclick="clearForm()">Clear Form</button>
<label>Generated notes</label><textarea id="output" readonly></textarea>
</div>
<script>
function v(id){return document.getElementById(id).value.trim()}
function add(lines,label,id){const val=v(id);if(val){lines.push('- '+label+': '+val)}}
function generateNotes(){let lines=[];lines.push('# Forecaster Notes');lines.push('');lines.push('## Quick setup');add(lines,'Main forecast problem','mainProblem');add(lines,'Biggest uncertainty','uncertainty');add(lines,'Changed from previous AFD','changed');lines.push('');lines.push('## Model guidance');add(lines,'Short-term model trend','shortModel');add(lines,'Ensemble/probability signal','ensemble');add(lines,'Temperature/heat/PoP notes','heatPop');add(lines,'Rain/QPF notes','rain');add(lines,'Confidence/model disagreement','modelConfidence');lines.push('');lines.push('## Current trends');add(lines,'Current location','nowLocation');add(lines,'Movement/timing','movement');add(lines,'Cloud/heating trend','clouds');add(lines,'Boundaries/focus areas','boundaries');add(lines,'Next 1 to 3 hours','nextHours');lines.push('');lines.push('## Impacts and wording');add(lines,'Public/DSS impacts','publicImpacts');add(lines,'Aviation impacts','aviation');add(lines,'Marine impacts','marine');add(lines,'Avoid saying','avoid');lines.push('');document.getElementById('output').value=lines.join('\n')}
async function copyNotes(){generateNotes();await navigator.clipboard.writeText(document.getElementById('output').value);alert('Copied notes to clipboard')}
function downloadNotes(){generateNotes();const blob=new Blob([document.getElementById('output').value],{type:'text/markdown'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='forecaster_notes.md';a.click();URL.revokeObjectURL(a.href)}
function clearForm(){document.querySelectorAll('textarea,input').forEach(e=>{if(e.id!=='output')e.value=''});document.getElementById('output').value=''}
</script>
</body>
</html>'''
    (outdir / "forecast_notes_form.html").write_text(html, encoding="utf-8")
