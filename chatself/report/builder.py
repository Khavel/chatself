"""
Builds a self-contained HTML report from chat analytics.
No external dependencies — pure Python + inline CSS/JS.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat

from chatself.analytics.patterns import PatternAnalyzer
from chatself.analytics.vocabulary import VocabularyAnalyzer
from chatself.analytics.relationships import RelationshipAnalyzer
from chatself.analytics.emojis import EmojiAnalyzer


class ReportBuilder:
    def __init__(self, chat: "Chat", my_name: str, lang: str = "es"):
        self.chat = chat
        self.my_name = my_name
        self.lang = lang

    def build(self) -> str:
        """Return the full HTML as a string."""
        patterns  = PatternAnalyzer(self.chat, self.my_name)
        vocab     = VocabularyAnalyzer(self.chat, self.my_name)
        relations = RelationshipAnalyzer(self.chat, self.my_name, self.lang)
        emojis    = EmojiAnalyzer(self.chat, self.my_name)

        p_summary = patterns.summary()
        v_summary = vocab.summary()
        e_summary = emojis.summary()
        drift     = relations.drift_over_time()
        gaps      = relations.silence_gaps()[:5]
        aff       = relations.affection_score()

        # Serialise to JSON for JS charts
        drift_json  = json.dumps(drift)
        emojis_json = json.dumps(e_summary["my_top_emojis"][:12])
        tics_json   = json.dumps([[t, c] for t, c in v_summary["verbal_tics"][:10]])

        participants = [p for p in self.chat.participants if p != self.my_name]
        other_name   = participants[0] if participants else "them"

        dr = self.chat.date_range
        date_range_str = (
            f"{dr[0].strftime('%b %Y')} → {dr[1].strftime('%b %Y')}" if dr else "—"
        )

        gaps_html = "".join(
            f"<li><strong>{g['days']} days</strong> &nbsp; {g['from']} → {g['to']}"
            f" &nbsp; <span class='badge'>resumed by {g['resumed_by']}</span></li>"
            for g in gaps
        ) or "<li>No significant gaps</li>"

        return HTML_TEMPLATE.format(
            chat_name=self.chat.name,
            my_name=self.my_name,
            other_name=other_name,
            date_range=date_range_str,
            total_msgs=p_summary["total_messages"],
            my_msgs=p_summary["my_messages"],
            their_msgs=p_summary["their_messages"],
            ratio=p_summary["message_ratio"],
            peak_hour=p_summary["peak_hour"],
            vocab_size=v_summary["vocabulary_size"],
            avg_len=v_summary["avg_length"],
            my_affection=aff.get("me", {}).get("pct", 0),
            their_affection=aff.get("them", {}).get("pct", 0),
            drift_json=drift_json,
            emojis_json=emojis_json,
            tics_json=tics_json,
            gaps_html=gaps_html,
            generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.write_text(self.build(), encoding="utf-8")
        return path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>chatself — {chat_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f0f13; --surface: #1a1a24; --border: #2a2a3a;
    --accent: #7c6af7; --accent2: #f76a8a; --text: #e8e8f0; --muted: #888;
    --green: #4ade80; --yellow: #fbbf24;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem; }}
  h1 {{ font-size: 2rem; font-weight: 700; }}
  h2 {{ font-size: 1.1rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 1rem; }}
  .subtitle {{ color: var(--muted); margin-top: .3rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.2rem; margin: 2rem 0; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.4rem; }}
  .stat {{ font-size: 2.4rem; font-weight: 700; color: var(--accent); }}
  .stat-label {{ color: var(--muted); font-size: .85rem; margin-top: .2rem; }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.4rem; margin-bottom: 1.2rem; }}
  .chart-wrap {{ position: relative; height: 220px; }}
  .emoji-row {{ display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .8rem; }}
  .emoji-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: .4rem .7rem; font-size: 1.1rem; display: flex; align-items: center; gap: .4rem; }}
  .emoji-count {{ font-size: .75rem; color: var(--muted); }}
  .badge {{ background: var(--accent); color: white; border-radius: 4px; padding: 1px 6px; font-size: .75rem; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: .4rem 0; border-bottom: 1px solid var(--border); color: var(--text); font-size: .9rem; }}
  li:last-child {{ border-bottom: none; }}
  .affection-bar {{ height: 8px; border-radius: 4px; background: var(--border); margin-top: .5rem; overflow: hidden; }}
  .affection-fill {{ height: 100%; border-radius: 4px; background: var(--accent2); transition: width .5s; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }}
  footer {{ color: var(--muted); font-size: .8rem; margin-top: 3rem; text-align: center; }}
  @media (max-width: 600px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>

<h1>🪞 {chat_name}</h1>
<p class="subtitle">{my_name} &nbsp;·&nbsp; {date_range} &nbsp;·&nbsp; Generated {generated}</p>

<div class="grid">
  <div class="card">
    <div class="stat">{total_msgs:,}</div>
    <div class="stat-label">Total messages</div>
  </div>
  <div class="card">
    <div class="stat">{ratio}×</div>
    <div class="stat-label">Your messages vs theirs</div>
  </div>
  <div class="card">
    <div class="stat">{peak_hour}h</div>
    <div class="stat-label">Peak activity hour</div>
  </div>
  <div class="card">
    <div class="stat">{vocab_size:,}</div>
    <div class="stat-label">Unique words used</div>
  </div>
</div>

<!-- Message drift chart -->
<div class="chart-card">
  <h2>Message balance over time</h2>
  <p class="subtitle" style="margin-bottom:1rem">Your % of messages per month — 50% = perfectly equal</p>
  <div class="chart-wrap"><canvas id="driftChart"></canvas></div>
</div>

<div class="two-col">

  <!-- Emojis -->
  <div class="card">
    <h2>Your emoji signature</h2>
    <div class="emoji-row" id="emojiRow"></div>
  </div>

  <!-- Verbal tics -->
  <div class="card">
    <h2>Your verbal tics</h2>
    <ul id="ticsList"></ul>
  </div>

</div>

<div class="two-col" style="margin-top:1.2rem">

  <!-- Affection -->
  <div class="card">
    <h2>Emotional tone</h2>
    <p style="font-size:.9rem;color:var(--muted);margin-bottom:.8rem">% of messages with affection markers</p>
    <div style="margin-bottom:.8rem">
      <div style="display:flex;justify-content:space-between;font-size:.85rem"><span>You</span><span>{my_affection}%</span></div>
      <div class="affection-bar"><div class="affection-fill" style="width:{my_affection}%"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;font-size:.85rem"><span>{other_name}</span><span>{their_affection}%</span></div>
      <div class="affection-bar"><div class="affection-fill" style="width:{their_affection}%;background:var(--accent)"></div></div>
    </div>
  </div>

  <!-- Silence gaps -->
  <div class="card">
    <h2>Longest silences</h2>
    <ul>{gaps_html}</ul>
  </div>

</div>

<footer>chatself · open source · your data stays on your machine</footer>

<script>
const drift = {drift_json};
const emojisData = {emojis_json};
const ticsData = {tics_json};

// Drift chart
const labels = drift.map(d => d.month);
const myPct  = drift.map(d => d.my_pct);

new Chart(document.getElementById('driftChart'), {{
  type: 'line',
  data: {{
    labels,
    datasets: [
      {{
        label: 'Your %',
        data: myPct,
        borderColor: '#7c6af7',
        backgroundColor: 'rgba(124,106,247,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
      }},
      {{
        label: '50% (equal)',
        data: labels.map(() => 50),
        borderColor: '#444',
        borderDash: [4, 4],
        pointRadius: 0,
        borderWidth: 1,
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#888' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#666', maxTicksLimit: 8 }}, grid: {{ color: '#222' }} }},
      y: {{ ticks: {{ color: '#666', callback: v => v + '%' }}, grid: {{ color: '#222' }}, min: 0, max: 100 }}
    }}
  }}
}});

// Emojis
const emojiRow = document.getElementById('emojiRow');
emojisData.forEach(e => {{
  const el = document.createElement('div');
  el.className = 'emoji-item';
  el.innerHTML = `<span>${{e.emoji}}</span><span class="emoji-count">${{e.count}}</span>`;
  emojiRow.appendChild(el);
}});

// Verbal tics
const ticsList = document.getElementById('ticsList');
ticsData.forEach(([phrase, count]) => {{
  const li = document.createElement('li');
  li.innerHTML = `<strong>${{phrase}}</strong> <span class="badge" style="float:right">${{count}}×</span>`;
  ticsList.appendChild(li);
}});
</script>
</body>
</html>
"""
