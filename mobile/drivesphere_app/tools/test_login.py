import requests

url = 'http://127.0.0.1:8000/api/auth/login/'
try:
    r = requests.post(url, json={'identifier': 'drivesphere', 'password': 'wrongpassword'}, timeout=5)
    print('STATUS', r.status_code)
    print('CT', r.headers.get('Content-Type'))
    print('TEXT', r.text)
except Exception as e:
    print('ERR', e)
