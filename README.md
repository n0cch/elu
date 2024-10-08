# elu
Entry Live Updater
<hr>

값 가져오기
```python
import requests

data = {
    'us': '아이디',
    'pw': '비밀번호',
    'p_id': '작품 아이디',
    'v_id': '변수 아이디',
}

response = requests.post('https://elu.vercel.app/get', json=data)
print(response.json())
```

값 바꾸기
```python
import requests

data = {
    'us': '아이디',
    'pw': '비밀번호',
    'p_id': '작품 아이디',
    'v_id': '변수 아이디',
    'data': '값'
}

response = requests.post('https://elu.vercel.app/set', json=data)

print(response.json())
```
