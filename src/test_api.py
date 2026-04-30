import requests

url = "http://localhost:8000/api/signals/generate"
data = {
  "symbol_x": "AAPL",
  "symbol_y": "GOOGL",
  "start": "2023-01-01",
  "end": "2024-01-01"
}
try:
    res = requests.post(url, json=data)
    print(res.status_code)
    print(res.json())
except Exception as e:
    print(e)
