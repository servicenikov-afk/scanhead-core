import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import webbrowser

def parse_progress_report(filepath: str) -> list:
    """Надёжный парсер progress_report.md — ищет блоки по дате."""
    content = Path(filepath).read_text(encoding='utf-8')
    
    print(f"📄 Размер файла: {len(content)} символов")
    print(f"📄 Строк: {len(content.splitlines())}")
    
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
                prev_line = lines[i - 1].strip()
                if prev_line.startswith('### '):
                    message = prev_line[4:].strip()
            
            insertions = 0
            deletions = 0
            files_changed = 0
            k = i + 1
            
            while k < len(lines):
                next_line = lines[k].strip()
                if not next_line:
                    k += 1
                    continue
                if date_pattern.match(next_line):
                    break
                if next_line.startswith('### '):
                    break
                
                stat_match = re.search(
                    r'(\d+)\s+files?\s+changed'
                    r'(?:,\s*(\d+)\s+insertions?\(\+\))?'
                    r'(?:,\s*(\d+)\s+deletions?\(-\))?',
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
    """Конвертирует YYYY-MM-DD в ДД.ММ.ГГГГ."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except Exception:
        return date_str

def generate_html(commits: list, output_path: str):
    """Генерирует интерактивный HTML с графиками."""
    if not commits:
        Path(output_path).write_text(
            '<html><body style="font-family:sans-serif;padding:40px;">'
            '<h1>⚠️ Нет данных для отображения</h1>'
            '<p>Проверьте формат файла progress_report.md</p>'
            '</body></html>',
            encoding='utf-8'
        )
        print(f"⚠️ Коммитов не найдено. Пустой отчёт: {output_path}")
        return
    
    # Группируем по дням
    by_date = defaultdict(lambda: {'commits': 0, 'insertions': 0, 'deletions': 0, 'files': 0})
    for c in commits:
        d = c['date']
        by_date[d]['commits'] += 1
        by_date[d]['insertions'] += c['insertions']
        by_date[d]['deletions'] += c['deletions']
        by_date[d]['files'] += c['files_changed']
    
    # ⬅️ СТАРЫЕ ДАТЫ СЛЕВА, НОВЫЕ СПРАВА (хронология)
    dates_sorted = sorted(by_date.keys())
    # Форматируем в ДД.ММ.ГГГГ для отображения
    dates_display = [format_date_rus(d) for d in dates_sorted]
    
    commits_per_day = [by_date[d]['commits'] for d in dates_sorted]
    insertions_per_day = [by_date[d]['insertions'] for d in dates_sorted]
    deletions_per_day = [by_date[d]['deletions'] for d in dates_sorted]
    files_per_day = [by_date[d]['files'] for d in dates_sorted]
    
    # Кумулятивные суммы (от старых к новым)
    cum_insertions, cum_deletions = [], []
    cum_i = cum_d = 0
    for d in dates_sorted:
        cum_i += by_date[d]['insertions']
        cum_d += by_date[d]['deletions']
        cum_insertions.append(cum_i)
        cum_deletions.append(cum_d)
    
    # Первый и последний коммит (по фактической дате)
    first_commit_date = format_date_rus(min(c['date'] for c in commits))
    last_commit_date = format_date_rus(max(c['date'] for c in commits))
    
    # Топ коммитов
    top_commits = sorted(commits, key=lambda x: x['insertions'] + x['deletions'], reverse=True)[:10]
    
    total_commits = len(commits)
    total_insertions = sum(c['insertions'] for c in commits)
    total_deletions = sum(c['deletions'] for c in commits)
    total_files = sum(c['files_changed'] for c in commits)
    
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    
    top_rows = ''.join(f"""
    <div class="commit-row">
      <div class="commit-date">{format_date_rus(c['date'])}</div>
      <div class="commit-msg">{esc(c['message'])}</div>
      <div class="commit-stats">
        <span class="ins">+{c['insertions']}</span>
        <span class="del">-{c['deletions']}</span>
      </div>
    </div>""" for c in top_commits)
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>ScanHead Core — Прогресс разработки</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: #fff; padding: 20px; min-height: 100vh;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  h1 {{ text-align: center; font-size: 2.2em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
  .subtitle {{ text-align: center; font-size: 1.1em; opacity: 0.9; margin-bottom: 10px; }}
  .date-range {{
    text-align: center; font-size: 1em; opacity: 0.85; margin-bottom: 25px;
    display: flex; justify-content: center; gap: 40px;
  }}
  .date-range span {{ color: #ffd700; font-weight: bold; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
  .stat-card {{
    background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
    border-radius: 12px; padding: 20px; text-align: center;
    border: 1px solid rgba(255,255,255,0.2); transition: transform 0.2s;
  }}
  .stat-card:hover {{ transform: translateY(-3px); }}
  .stat-value {{ font-size: 2.5em; font-weight: bold; color: #ffd700; }}
  .stat-label {{ font-size: 0.9em; opacity: 0.85; margin-top: 5px; }}
  .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .chart-box {{
    background: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px;
    color: #333; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  }}
  .chart-box.full {{ grid-column: 1 / -1; }}
  .chart-box h2 {{ font-size: 1.2em; margin-bottom: 15px; color: #1e3c72; border-bottom: 2px solid #2a5298; padding-bottom: 8px; }}
  .top-commits {{ background: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px; color: #333; margin-top: 20px; }}
  .top-commits h2 {{ font-size: 1.2em; margin-bottom: 15px; color: #1e3c72; border-bottom: 2px solid #2a5298; padding-bottom: 8px; }}
  .commit-row {{ display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid #eee; transition: background 0.15s; }}
  .commit-row:hover {{ background: #f5f5f5; }}
  .commit-msg {{ flex: 1; font-size: 0.9em; }}
  .commit-date {{ color: #666; font-size: 0.85em; margin-right: 15px; min-width: 90px; }}
  .commit-stats {{ display: flex; gap: 10px; font-size: 0.85em; }}
  .ins {{ color: #28a745; font-weight: bold; }}
  .del {{ color: #dc3545; font-weight: bold; }}
  @media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 ScanHead Core — Прогресс разработки</h1>
  <div class="subtitle">Всего коммитов: {total_commits}</div>
  <div class="date-range">
    <div>🚩 Первый коммит: <span>{first_commit_date}</span></div>
    <div>🏁 Последний коммит: <span>{last_commit_date}</span></div>
  </div>
  
  <div class="stats-grid">
    <div class="stat-card"><div class="stat-value">{total_commits}</div><div class="stat-label">Всего коммитов</div></div>
    <div class="stat-card"><div class="stat-value" style="color:#28a745">+{total_insertions:,}</div><div class="stat-label">Строк добавлено</div></div>
    <div class="stat-card"><div class="stat-value" style="color:#dc3545">-{total_deletions:,}</div><div class="stat-label">Строк удалено</div></div>
    <div class="stat-card"><div class="stat-value">{total_files:,}</div><div class="stat-label">Изменений файлов</div></div>
  </div>
  
  <div class="chart-grid">
    <div class="chart-box full"><h2>📈 Активность по дням (коммиты)</h2><canvas id="commitsChart" height="80"></canvas></div>
    <div class="chart-box"><h2>➕ Добавлено строк по дням</h2><canvas id="insChart"></canvas></div>
    <div class="chart-box"><h2>➖ Удалено строк по дням</h2><canvas id="delChart"></canvas></div>
    <div class="chart-box full"><h2>📊 Кумулятивный прогресс (накопленный объём кода)</h2><canvas id="cumChart" height="80"></canvas></div>
    <div class="chart-box full"><h2>📁 Изменения файлов по дням</h2><canvas id="filesChart" height="80"></canvas></div>
  </div>
  
  <div class="top-commits">
    <h2>🏆 Топ-10 самых масштабных коммитов</h2>
    {top_rows}
  </div>
</div>

<script>
const dates = {dates_display};
const commitsPerDay = {commits_per_day};
const insPerDay = {insertions_per_day};
const delPerDay = {deletions_per_day};
const filesPerDay = {files_per_day};
const cumIns = {cum_insertions};
const cumDel = {cum_deletions};

Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

new Chart(document.getElementById('commitsChart'), {{
  type: 'bar',
  data: {{ labels: dates, datasets: [{{ label: 'Коммитов', data: commitsPerDay, backgroundColor: 'rgba(54, 162, 235, 0.7)', borderColor: 'rgba(54, 162, 235, 1)', borderWidth: 1 }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }}
}});

new Chart(document.getElementById('insChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [{{ label: 'Добавлено строк', data: insPerDay, borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.2)', fill: true, tension: 0.3 }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});

new Chart(document.getElementById('delChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [{{ label: 'Удалено строк', data: delPerDay, borderColor: '#dc3545', backgroundColor: 'rgba(220, 53, 69, 0.2)', fill: true, tension: 0.3 }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});

new Chart(document.getElementById('cumChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Накоплено добавлений', data: cumIns, borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.1)', fill: true, tension: 0.3 }},
    {{ label: 'Накоплено удалений', data: cumDel, borderColor: '#dc3545', backgroundColor: 'rgba(220, 53, 69, 0.1)', fill: true, tension: 0.3 }}
  ] }},
  options: {{ responsive: true, interaction: {{ mode: 'index', intersect: false }} }}
}});

new Chart(document.getElementById('filesChart'), {{
  type: 'bar',
  data: {{ labels: dates, datasets: [{{ label: 'Файлов изменено', data: filesPerDay, backgroundColor: 'rgba(255, 193, 7, 0.7)', borderColor: 'rgba(255, 193, 7, 1)', borderWidth: 1 }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
</body>
</html>'''
    
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"✅ Отчёт сгенерирован: {output_path}")

if __name__ == '__main__':
    commits = parse_progress_report('progress_report.md')
    print(f"\n📊 Распарсено коммитов: {len(commits)}")
    if commits:
        print(f"📅 Первый коммит: {format_date_rus(min(c['date'] for c in commits))}")
        print(f"📅 Последний коммит: {format_date_rus(max(c['date'] for c in commits))}")
        print(f"📊 Суммарно: +{sum(c['insertions'] for c in commits):,} / -{sum(c['deletions'] for c in commits):,} строк")
    generate_html(commits, 'progress_dashboard.html')
    
    webbrowser.open(f'file://{Path("progress_dashboard.html").absolute()}')