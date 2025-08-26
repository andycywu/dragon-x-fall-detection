"""
Merge ONNX validation report and QAI Hub compile report into a single JSON.
- Reads: src/qaihub_optimize/onnx_validation_report.json
- Finds latest: src/qaihub_optimize/qai_hub_compile_report_*.html
- Extracts model rows (Model Name + Error cell + Job ID if present)
- Attempts to fetch job logs via QAIHubClient.get_job_logs(job_id)
- Writes: src/qaihub_optimize/merged_quantize_report.json
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent.parent
ONNX_REPORT = BASE / 'onnx_validation_report.json'
HTML_DIR = BASE
OUT_PATH = BASE / 'merged_quantize_report.json'

# import client wrapper if available
try:
    from ..modules.qaihub_client import get_qaihub_client
    client_available = True
except Exception:
    get_qaihub_client = None
    client_available = False


def find_latest_html():
    files = list(HTML_DIR.glob('qai_hub_compile_report_*.html'))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def parse_html(html_path: Path):
    data = {}
    with open(html_path, 'r', encoding='utf-8') as f:
        text = f.read()
    soup = BeautifulSoup(text, 'html.parser')
    table = soup.find('table')
    if not table:
        return data
    rows = table.find_all('tr')
    for tr in rows[1:]:
        cols = tr.find_all('td')
        if len(cols) < 5:
            continue
        model = cols[0].get_text(strip=True)
        status = cols[1].get_text(strip=True)
        job_id = ''
        # try to extract job_id from dashboard link
        link = cols[3].find('a')
        if link and link.get('href'):
            m = re.search(r'/jobs/([a-z0-9]+)', link['href'])
            if m:
                job_id = m.group(1)
        # fallback: try to find job id in error cell
        error_text = cols[4].get_text(separator='\n').strip()
        if not job_id:
            m2 = re.search(r'Job ID[:\s]*([a-z0-9]+)', error_text, re.IGNORECASE)
            if m2:
                job_id = m2.group(1)

        data[model] = {
            'model': model,
            'status': status,
            'job_id': job_id,
            'error_text': error_text
        }
    return data


def load_onnx_report():
    if not ONNX_REPORT.exists():
        return {}
    with open(ONNX_REPORT, 'r', encoding='utf-8') as f:
        arr = json.load(f)
    by_name = {}
    for item in arr:
        name = Path(item['model']).stem
        by_name[name] = item
    return by_name


def main():
    onnx = load_onnx_report()
    html = find_latest_html()
    if not html:
        print('No HTML report found')
        return
    html_data = parse_html(html)

    merged = {}
    for model_name, info in html_data.items():
        entry = {'model': model_name, 'qai': info}
        if model_name in onnx:
            entry['onnx_validation'] = onnx[model_name]
        else:
            entry['onnx_validation'] = None

        job_id = info.get('job_id')
        logs = None
        if job_id and client_available:
            try:
                cli = get_qaihub_client()
                logs = cli.get_job_logs(job_id)
            except Exception as e:
                logs = f'failed to fetch logs: {e}'
        entry['job_logs'] = logs
        merged[model_name] = entry

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f'Wrote merged report to {OUT_PATH}')

if __name__ == '__main__':
    main()
