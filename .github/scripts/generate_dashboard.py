#!/usr/bin/env python3
# --- .github/scripts/generate_dashboard.py ---
# Полная автоматизация: парсинг git log → dashboard.html

import re
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

REPORT_PATH = Path("progress_report.md")
OUTPUT_PATH = Path("docs/dashboard.html")
SINCE_DATE = "2026-02-01"  # ← измени под свой проект


def generate_progress_report():
    """Генерирует progress_report.md из git log."""
    cmd = [
        "git", "log",
        f"--since={SINCE_DATE}",
        "--pretty=format:### %s%n**%ad** | %an%n",
        "--date=short",
        "--stat"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
    
    if result.returncode != 0:
        print(f"❌ Ошибка git log: {result.stderr}")
        return False
    
    REPORT_PATH.write_text(result.stdout, encoding='utf-8')
    print(f"✅ progress_report.md сгенерирован ({len(result.stdout)} символов)")
    return True


def parse_progress_report(filepath: Path) -> list:
    """Парсит progress_report.md в список коммитов."""
    if not filepath.exists():
        return []
    
    content = filepath.read_text(encoding='utf-8')
    commits = []
    lines = content.splitlines()
    date_pattern = re.compile(r'^\*\*(\d{4}-\d{2}-\d{2})\*\*\s*\|\s*(.+)$')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = date_pattern.match(line)
        if match:
            date_str = match.group(1)
            author = match.group(2).strip()
            message = ""
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.startswith('### '):
                    message = prev_line[4:].strip()
            
            insertions = deletions = files_changed = 0
            k = i + 1
            while k < len(lines):
                next_line = lines[k].strip()
                if not next_line:
                    k += 1
                    continue
                if date_pattern.match(next_line) or next_line.startswith('### '):
                    break
                stat_match = re.search(
                    r'(\d+)\s+files?\s+changed(?:,\s*(\d+)\s+insertions?\(\+\))?(?:,\s*(\d+)\s+deletions?\(-\))?',
                    next_line
                )
                if stat_match:
                    files_changed = int(stat_match.group(1))
                    insertions = int(stat_match.group(2) or 0)
                    deletions = int(stat_match.group(3) or 0)
                k += 1
            
            if message:
                commits.append({
                    'message': message,
                    'date': date_str,
                    'author': author,
                    'insertions': insertions,
                    'deletions': deletions,
                    'files_changed': files_changed
                })
        i += 1
    
    return commits


def format_date_rus(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')
    except Exception:
        return date_str


def generate_html(commits: list, output_path: Path):
    """Генерирует dashboard.html из списка коммитов."""
    if not commits:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            '<html><body><h1>📊 Нет данных</h1>'
            '<p>Коммитов за период не найдено</p></body></html>',
            encoding='utf-8'
        )
        print("⚠️ Нет коммитов для отображения")
        return

    by_date = defaultdict(lambda: {'commits': 0, 'insertions': 0, 'deletions': 0, 'files': 0})
    for c in commits:
        d = c['date']
        by_date[d]['commits'] += 1
        by_date[d]['insertions'] += c['insertions']
        by_date[d]['deletions'] += c['deletions']
        by_date[d]['files'] += c['files_changed']

    dates_sorted = sorted(by_date.keys())
    dates_display = [format_date_rus(d) for d in dates_sorted]

    commits_per_day = [by_date[d]['commits'] for d in dates_sorted]
    insertions_per_day = [by_date[d]['insertions'] for d in dates_sorted]
    deletions_per_day = [by_date[d]['deletions'] for d in dates_sorted]
    files_per_day = [by_date[d]['files'] for d in dates_sorted]

    cum_i = cum_d = 0
    cum_insertions = []
    cum_deletions = []
    for d in dates_sorted:
        cum_i += by_date[d]['insertions']
        cum_d += by_date[d]['deletions']
        cum_insertions.append(cum_i)
        cum_deletions.append(cum_d)

    first_commit_date = format_date_rus(min(c['date'] for c in commits))
    last_commit_date = format_date_rus(max(c['date'] for c in commits))

    top_commits = sorted(commits, key=lambda x: x['insertions'] + x['deletions'], reverse=True)[:10]

    total_commits = len(commits)
    total_insertions = sum(c['insertions'] for c in commits)
    total_deletions = sum(c['deletions'] for c in commits)
    total_files = sum(c['files_changed'] for c in commits)

    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    top_rows = ''.join(
        f'<tr><td>{format_date_rus(c["date"])}</td>'
        f'<td>{esc(c["message"])}</td>'
        f'<td style="color:green;text-align:right">+{c["insertions"]}</td>'
        f'<td style="color:red;text-align:right">-{c["deletions"]}</td></tr>'
        for c in top_commits
    )

    max_insertions = max(insertions_per_day) if insertions_per_day else 1
    max_deletions = max(deletions_per_day) if deletions_per_day else 1
    max_commits = max(commits_per_day) if commits_per_day else 1
    max_files = max(files_per_day) if files_per_day else 1

    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 ScanHead Core — Прогресс</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat-box {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-box .num {{ font-size: 2em; font-weight: bold; }}
        .stat-box .label {{ opacity: 0.9; font-size: 0.9em; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-bottom: 15px; color: #555; }}
        .card .chart-container {{ height: 250px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f0f0f0; font-weight: 600; }}
        .footer {{ text-align: center; color: #999; font-size: 0.8em; margin-top: 30px; }}
        @media (max-width: 600px) {{
            .stats {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 ScanHead Core — Прогресс разработки</h1>

    <div class="stats">
        <div class="stat-box"><div class="num">{total_commits}</div><div class="label">Всего коммитов</div></div>
        <div class="stat-box"><div class="num">+{total_insertions:,}</div><div class="label">Строк добавлено</div></div>
        <div class="stat-box"><div class="num">-{total_deletions:,}</div><div class="label">Строк удалено</div></div>
        <div class="stat-box"><div class="num">{total_files:,}</div><div class="label">Изменений файлов</div></div>
    </div>

    <p style="color:#666;margin-bottom:20px;">
        🚩 Первый коммит: <b>{first_commit_date}</b> &nbsp;|&nbsp; 🏁 Последний: <b>{last_commit_date}</b>
        &nbsp;|&nbsp; 📅 Период: с {SINCE_DATE}
    </p>

    <div class="card">
        <h3>📈 Активность по дням (коммиты)</h3>
        <div class="chart-container"><canvas id="commitsChart"></canvas></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div class="card">
            <h3>➕ Добавлено</h3>
            <div class="chart-container"><canvas id="insertionsChart"></canvas></div>
        </div>
        <div class="card">
            <h3>➖ Удалено</h3>
            <div class="chart-container"><canvas id="deletionsChart"></canvas></div>
        </div>
    </div>

    <div class="card">
        <h3>📊 Кумулятивный прогресс</h3>
        <div class="chart-container"><canvas id="cumulativeChart"></canvas></div>
    </div>

    <div class="card">
        <h3>📁 Изменения файлов по дням</h3>
        <div class="chart-container"><canvas id="filesChart"></canvas></div>
    </div>

    <div class="card">
        <h3>🏆 Топ-10 самых масштабных коммитов</h3>
        <table>
            <thead><tr><th>Дата</th><th>Сообщение</th><th style="text-align:right">+</th><th style="text-align:right">-</th></tr></thead>
            <tbody>{top_rows}</tbody>
        </table>
    </div>

    <div class="footer">Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} · Автоматическая генерация</div>
</div>

<script>
const labels = {dates_display};

function createBarChart(id, label, data, color, bg, maxVal) {{
    new Chart(document.getElementById(id), {{
        type: 'bar',
        data: {{ labels, datasets: [{{ label, data, backgroundColor: bg, borderColor: color, borderWidth: 1 }}] }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{ y: {{ beginAtZero: true, max: Math.max(maxVal * 1.15, 5) }} }}
        }}
    }});
}}

createBarChart('commitsChart', 'Коммитов', {commits_per_day}, '#36A2EB', 'rgba(54,162,235,0.6)', {max_commits});
createBarChart('insertionsChart', 'Добавлено', {insertions_per_day}, '#4BC0C0', 'rgba(75,192,192,0.6)', {max_insertions});
createBarChart('deletionsChart', 'Удалено', {deletions_per_day}, '#FF6384', 'rgba(255,99,132,0.6)', {max_deletions});
createBarChart('filesChart', 'Файлов', {files_per_day}, '#FFCE56', 'rgba(255,206,86,0.6)', {max_files});

new Chart(document.getElementById('cumulativeChart'), {{
    type: 'line',
    data: {{
        labels,
        datasets: [
            {{ label: 'Добавлено (накоп.)', data: {cum_insertions}, borderColor: '#4BC0C0', backgroundColor: 'rgba(75,192,192,0.1)', fill: true, tension: 0.2 }},
            {{ label: 'Удалено (накоп.)', data: {cum_deletions}, borderColor: '#FF6384', backgroundColor: 'rgba(255,99,132,0.1)', fill: true, tension: 0.2 }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ y: {{ beginAtZero: true }} }}
    }}
}});
</script>
</body>
</html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    print(f"✅ Dashboard сгенерирован: {output_path}")


def main():
    print("🚀 Запуск генерации дашборда...")
    
    # Шаг 1: Генерация progress_report.md из git log
    if not generate_progress_report():
        print("❌ Не удалось сгенерировать progress_report.md")
        return 1
    
    # Шаг 2: Парсинг progress_report.md
    commits = parse_progress_report(REPORT_PATH)
    print(f"📊 Найдено коммитов: {len(commits)}")
    
    if commits:
        print(f"   Первый: {format_date_rus(min(c['date'] for c in commits))}")
        print(f"   Последний: {format_date_rus(max(c['date'] for c in commits))}")
        total_i = sum(c['insertions'] for c in commits)
        total_d = sum(c['deletions'] for c in commits)
        print(f"   +{total_i:,} / -{total_d:,} строк")
    
    # Шаг 3: Генерация dashboard.html
    generate_html(commits, OUTPUT_PATH)
    
    # Шаг 4: Удаление progress_report.md (временный файл)
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()
        print(f"🗑️ Удалён временный файл: {REPORT_PATH}")
    
    print("✅ Готово!")
    return 0


if __name__ == '__main__':
    exit(main())