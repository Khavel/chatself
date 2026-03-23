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
            f"<div class='silence-item'>"
            f"<div class='silence-days'>{g['days']}<small>days</small></div>"
            f"<div class='silence-detail'><strong>{g['from']}</strong> → <strong>{g['to']}</strong>"
            f"<br><span class='resumed-badge'>↩ resumed by {g['resumed_by']}</span></div>"
            f"</div>"
            for g in gaps
        ) or "<div style='color:var(--muted2);font-size:.85rem'>No significant gaps</div>"

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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #080810;
    --surface: #12121e;
    --surface2: #1a1a2e;
    --border: #ffffff0f;
    --border2: #ffffff18;
    --accent: #7c6af7;
    --accent2: #f76a8a;
    --accent3: #38bdf8;
    --text: #f0f0fa;
    --muted: #6b6b8a;
    --muted2: #9090b0;
    --green: #4ade80;
    --purple-glow: rgba(124,106,247,0.15);
    --pink-glow: rgba(247,106,138,0.12);
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 15px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ── Layout ── */
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }}

  /* ── Hero header ── */
  .hero {{
    position: relative;
    padding: 3rem 2.5rem 2.5rem;
    background: linear-gradient(135deg, #12121e 0%, #1a1030 50%, #120a20 100%);
    border: 1px solid var(--border2);
    border-radius: 20px;
    margin-bottom: 2rem;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(124,106,247,0.2) 0%, transparent 70%);
    pointer-events: none;
  }}
  .hero::after {{
    content: '';
    position: absolute;
    bottom: -80px; left: 20%;
    width: 300px; height: 200px;
    background: radial-gradient(circle, rgba(247,106,138,0.1) 0%, transparent 70%);
    pointer-events: none;
  }}
  .hero-eyebrow {{
    font-size: .75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: var(--accent);
    margin-bottom: .6rem;
  }}
  .hero h1 {{
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    font-weight: 800;
    letter-spacing: -.02em;
    background: linear-gradient(135deg, #fff 30%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: .5rem;
  }}
  .hero-meta {{
    font-size: .85rem;
    color: var(--muted2);
    display: flex;
    flex-wrap: wrap;
    gap: .4rem 1.2rem;
    margin-top: .8rem;
  }}
  .hero-meta span {{ display: flex; align-items: center; gap: .3rem; }}

  /* ── Section title ── */
  .section-title {{
    font-size: .7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .14em;
    color: var(--muted);
    margin-bottom: 1rem;
  }}

  /* ── Stat grid ── */
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: .9rem;
    margin-bottom: 2rem;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color .2s, transform .2s;
  }}
  .stat-card:hover {{ border-color: var(--border2); transform: translateY(-2px); }}
  .stat-card::before {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 14px;
    opacity: 0;
    transition: opacity .3s;
  }}
  .stat-card.purple::before {{ background: var(--purple-glow); opacity: 1; }}
  .stat-card.pink::before   {{ background: var(--pink-glow);   opacity: 1; }}
  .stat-icon {{ font-size: 1.4rem; margin-bottom: .5rem; display: block; }}
  .stat-value {{
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -.03em;
    line-height: 1;
    color: var(--text);
  }}
  .stat-card.purple .stat-value {{ color: var(--accent); }}
  .stat-card.pink   .stat-value {{ color: var(--accent2); }}
  .stat-card.blue   .stat-value {{ color: var(--accent3); }}
  .stat-label {{
    font-size: .78rem;
    color: var(--muted2);
    margin-top: .35rem;
    font-weight: 500;
  }}

  /* ── Cards ── */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.6rem;
  }}
  .chart-card {{ margin-bottom: 1.5rem; }}
  .chart-wrap {{ position: relative; height: 230px; margin-top: 1rem; }}

  /* ── Two col ── */
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }}

  /* ── Emoji pills ── */
  .emoji-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    margin-top: 1rem;
  }}
  .emoji-pill {{
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 999px;
    padding: .35rem .85rem;
    display: flex;
    align-items: center;
    gap: .5rem;
    font-size: 1.05rem;
    transition: transform .15s;
  }}
  .emoji-pill:hover {{ transform: scale(1.08); }}
  .emoji-count {{ font-size: .72rem; color: var(--muted2); font-weight: 600; }}

  /* ── Verbal tics ── */
  .tic-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: .55rem 0;
    border-bottom: 1px solid var(--border);
    font-size: .88rem;
  }}
  .tic-row:last-child {{ border-bottom: none; }}
  .tic-phrase {{ color: var(--text); font-weight: 500; }}
  .tic-bar-wrap {{ flex: 1; margin: 0 .8rem; height: 4px; background: var(--border2); border-radius: 2px; overflow: hidden; }}
  .tic-bar {{ height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }}
  .tic-count {{ font-size: .75rem; color: var(--muted); white-space: nowrap; }}

  /* ── Affection ── */
  .aff-row {{ margin-bottom: 1.1rem; }}
  .aff-row:last-child {{ margin-bottom: 0; }}
  .aff-header {{
    display: flex;
    justify-content: space-between;
    font-size: .85rem;
    margin-bottom: .4rem;
    font-weight: 500;
  }}
  .aff-pct {{ color: var(--accent2); font-weight: 700; }}
  .aff-track {{ height: 6px; border-radius: 3px; background: var(--border2); overflow: hidden; }}
  .aff-fill {{ height: 100%; border-radius: 3px; transition: width .8s cubic-bezier(.4,0,.2,1); }}

  /* ── Silences timeline ── */
  .silence-list {{ margin-top: .8rem; }}
  .silence-item {{
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: .7rem 0;
    border-bottom: 1px solid var(--border);
    font-size: .85rem;
  }}
  .silence-item:last-child {{ border-bottom: none; }}
  .silence-days {{
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--accent2);
    min-width: 3rem;
    line-height: 1;
  }}
  .silence-days small {{ font-size: .6rem; color: var(--muted); font-weight: 500; display: block; }}
  .silence-detail {{ color: var(--muted2); line-height: 1.5; }}
  .silence-detail strong {{ color: var(--text); font-weight: 600; }}
  .resumed-badge {{
    display: inline-block;
    background: rgba(124,106,247,.15);
    color: var(--accent);
    border-radius: 4px;
    padding: 1px 7px;
    font-size: .72rem;
    font-weight: 600;
    margin-top: .2rem;
  }}

  /* ── Footer ── */
  .footer {{
    margin-top: 3rem;
    text-align: center;
    color: var(--muted);
    font-size: .8rem;
  }}
  .footer a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }}
  .footer a:hover {{ text-decoration: underline; }}
  .install-hint {{
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 8px;
    padding: .4rem 1rem;
    font-family: 'Courier New', monospace;
    font-size: .8rem;
    color: var(--accent3);
    margin: .7rem auto 0;
  }}

  @media (max-width: 600px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .stat-grid {{ grid-template-columns: 1fr 1fr; }}
    .hero {{ padding: 2rem 1.4rem; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <!-- Hero -->
  <div class="hero">
    <div class="hero-eyebrow">chatself · conversation analysis</div>
    <h1>{chat_name}</h1>
    <div class="hero-meta">
      <span>👤 {my_name}</span>
      <span>📅 {date_range}</span>
      <span>🕐 generated {generated}</span>
    </div>
  </div>

  <!-- Stats -->
  <div class="section-title">At a glance</div>
  <div class="stat-grid">
    <div class="stat-card purple">
      <span class="stat-icon">💬</span>
      <div class="stat-value">{total_msgs:,}</div>
      <div class="stat-label">total messages</div>
    </div>
    <div class="stat-card pink">
      <span class="stat-icon">⚖️</span>
      <div class="stat-value">{ratio}×</div>
      <div class="stat-label">your msgs vs theirs</div>
    </div>
    <div class="stat-card blue">
      <span class="stat-icon">🌙</span>
      <div class="stat-value">{peak_hour}h</div>
      <div class="stat-label">peak activity hour</div>
    </div>
    <div class="stat-card">
      <span class="stat-icon">📖</span>
      <div class="stat-value">{vocab_size:,}</div>
      <div class="stat-label">unique words used</div>
    </div>
  </div>

  <!-- Drift chart -->
  <div class="card chart-card">
    <div class="section-title">Who talked more — month by month</div>
    <div style="font-size:.82rem;color:var(--muted2)">Your share of the conversation. The dashed line is 50/50. When it dips, they were carrying it. When it climbs, you were.</div>
    <div class="chart-wrap"><canvas id="driftChart"></canvas></div>
  </div>

  <!-- Emojis + Tics -->
  <div class="two-col">
    <div class="card">
      <div class="section-title">Your emoji signature</div>
      <div class="emoji-grid" id="emojiRow"></div>
    </div>
    <div class="card">
      <div class="section-title">Your verbal tics</div>
      <div id="ticsList" style="margin-top:.8rem"></div>
    </div>
  </div>

  <!-- Affection + Silences -->
  <div class="two-col" style="margin-top:1rem">
    <div class="card">
      <div class="section-title">Emotional tone</div>
      <div style="font-size:.78rem;color:var(--muted2);margin-bottom:1rem">% of messages with affection markers (💙 ❤️ miss, love, 😊…)</div>
      <div class="aff-row">
        <div class="aff-header"><span>You</span><span class="aff-pct">{my_affection}%</span></div>
        <div class="aff-track"><div class="aff-fill" style="width:{my_affection}%;background:linear-gradient(90deg,var(--accent2),#ff9a9e)"></div></div>
      </div>
      <div class="aff-row">
        <div class="aff-header"><span>{other_name}</span><span class="aff-pct">{their_affection}%</span></div>
        <div class="aff-track"><div class="aff-fill" style="width:{their_affection}%;background:linear-gradient(90deg,var(--accent),#a78bfa)"></div></div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Longest silences</div>
      <div class="silence-list">{gaps_html}</div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div>made with <a href="https://github.com/Khavel/chatself">chatself</a> · your data never leaves your machine</div>
    <div class="install-hint">pip install chatself</div>
  </div>

</div><!-- /wrap -->

<script>
const drift = {drift_json};
const emojisData = {emojis_json};
const ticsData = {tics_json};

// ── Drift chart
const labels = drift.map(d => d.month);
const myPct  = drift.map(d => d.my_pct);

const ctx = document.getElementById('driftChart').getContext('2d');
const grad = ctx.createLinearGradient(0, 0, 0, 230);
grad.addColorStop(0,   'rgba(124,106,247,0.25)');
grad.addColorStop(1,   'rgba(124,106,247,0)');

new Chart(ctx, {{
  type: 'line',
  data: {{
    labels,
    datasets: [
      {{
        label: 'Your %',
        data: myPct,
        borderColor: '#7c6af7',
        backgroundColor: grad,
        fill: true,
        tension: 0.45,
        pointRadius: 4,
        pointBackgroundColor: '#7c6af7',
        pointBorderColor: '#080810',
        pointBorderWidth: 2,
        borderWidth: 2.5,
      }},
      {{
        label: '50% equal',
        data: labels.map(() => 50),
        borderColor: 'rgba(255,255,255,0.12)',
        borderDash: [5, 5],
        pointRadius: 0,
        borderWidth: 1.5,
        fill: false,
      }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ labels: {{ color: '#6b6b8a', font: {{ size: 11 }} }} }},
      tooltip: {{
        backgroundColor: '#1a1a2e',
        borderColor: '#ffffff18',
        borderWidth: 1,
        titleColor: '#f0f0fa',
        bodyColor: '#9090b0',
        padding: 10,
        callbacks: {{ label: ctx => ` ${{ctx.parsed.y}}% of messages` }}
      }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#4a4a6a', font: {{ size: 11 }}, maxTicksLimit: 10 }}, grid: {{ color: '#ffffff06' }} }},
      y: {{
        ticks: {{ color: '#4a4a6a', font: {{ size: 11 }}, callback: v => v + '%' }},
        grid: {{ color: '#ffffff06' }},
        min: 0, max: 100
      }}
    }}
  }}
}});

// ── Emojis
const emojiRow = document.getElementById('emojiRow');
emojisData.forEach(e => {{
  const el = document.createElement('div');
  el.className = 'emoji-pill';
  el.innerHTML = `<span>${{e.emoji}}</span><span class="emoji-count">${{e.count}}×</span>`;
  emojiRow.appendChild(el);
}});

// ── Verbal tics
const ticsList = document.getElementById('ticsList');
const maxCount = ticsData.length ? ticsData[0][1] : 1;
ticsData.forEach(([phrase, count]) => {{
  const pct = Math.round((count / maxCount) * 100);
  const row = document.createElement('div');
  row.className = 'tic-row';
  row.innerHTML = `
    <span class="tic-phrase">${{phrase}}</span>
    <div class="tic-bar-wrap"><div class="tic-bar" style="width:${{pct}}%"></div></div>
    <span class="tic-count">${{count}}×</span>`;
  ticsList.appendChild(row);
}});
</script>
</body>
</html>
"""
