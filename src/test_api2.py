import requests

url = "http://localhost:8000/api/signals/generate"
data = {
  "symbol_x": "AAPL",
  "symbol_y": "GOOGL",
  "start": "2023-01-01",
  "end": "2026-04-29",
  "entry_threshold": 2.0,
  "exit_threshold": 0.5,
  "target_gross_exposure": 1.0
}
try:
    res = requests.post(url, json=data)
    print(res.status_code)
    print(res.text[:500])
except Exception as e:
    print(e)
