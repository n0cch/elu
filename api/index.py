from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import websocket

app = Flask(__name__)

def signin(username, password):
    session = requests.Session()
    login_page = session.get('https://playentry.org/signin')
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

    login_headers = {
        'CSRF-Token': csrf_token,
        'Content-Type': 'application/json'
    }

    login_query = '''
    mutation ($username: String!, $password: String!, $rememberme: Boolean) {
        signinByUsername (username: $username, password: $password, rememberme: $rememberme) {
            id
            username
            nickname
        }
    }
    '''

    login_variables = {
        'username': username,
        'password': password,
        'rememberme': False
    }

    login_response = session.post('https://playentry.org/graphql',
                                headers=login_headers,
                                json={'query': login_query, 'variables': login_variables})
    login_data = login_response.json()

    if 'errors' in login_data:
        return None, None, None

    main_page = session.get('https://playentry.org')
    soup = BeautifulSoup(main_page.text, 'html.parser')
    next_data = json.loads(soup.select_one('#__NEXT_DATA__').get_text())
    x_token = next_data['props']['initialState']['common']['user']['xToken']

    return session, x_token, csrf_token

def ws_query(session, x_token, csrf_token, project_id):
    graphql_headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'csrf-token': csrf_token,
        'x-token': x_token
    }

    graphql_query = '''
    query GET_CLOUD_SERVER_INFO($id: ID!) {
        cloudServerInfo(id: $id) {
            url
            query
        }
    }
    '''

    graphql_variables = {'id': project_id}
    graphql_response = session.post('https://playentry.org/graphql',
                                    headers=graphql_headers,
                                    json={'query': graphql_query, 'variables': graphql_variables})

    cloud_server_info = graphql_response.json()['data']['cloudServerInfo']
    query_token = cloud_server_info['query']

    return f'wss://playentry.org/cv/?type=undefined&q={query_token}&EIO=3&transport=websocket'

@app.route('/')
def main():
    return jsonify('https://github.com/n0cch/elu')

@app.route('/set', methods=['POST'])
def update_variable():
    data = request.json
    username = data.get('us')
    password = data.get('pw')
    project_id = data.get('p_id')
    v_id = data.get('v_id')
    value = data.get('data')

    if not username or not password or not project_id or not v_id or not value:
        return jsonify({'error': '필수 정보가 누락되었습니다.'}), 400

    session, x_token, csrf_token = signin(username, password)
    if not session:
        return jsonify({"error": "로그인 실패: 아이디나 비밀번호를 확인하세요."}), 401

    ws_url = ws_query(session, x_token, csrf_token, project_id)

    ws = websocket.create_connection(ws_url)
    ws.send(f'420["action",{{"_id":"{project_id}","id":"{v_id}","variableType":"variable","type":"set","value":"{value}"}}]')
    ws.close()

    return jsonify({'message': f'"{project_id}"의 "{v_id}"가 "{value}"로 변경되었습니다.'})

@app.route('/get', methods=['POST'])
def get_variable():
    data = request.json
    username = data.get('us')
    password = data.get('pw')
    project_id = data.get('p_id')
    v_id = data.get('v_id')

    if not username or not password or not project_id or not v_id:
        return jsonify({'error': '필수 정보가 누락되었습니다.'}), 400

    session, x_token, csrf_token = signin(username, password)
    if not session:
        return jsonify({"error": "로그인 실패: 아이디나 비밀번호를 확인하세요."}), 401

    ws_url = ws_query(session, x_token, csrf_token, project_id)

    ws = websocket.create_connection(ws_url)

    value = None
    while True:
        message = ws.recv()
        if message.startswith('42'):
            try:
                data = json.loads(message[2:])[1]
                variables = data.get('variables', [])
                for variable in variables:
                    if variable['id'] == v_id:
                        value = variable['value']
                        break
            except Exception as e:
                value = f'값 가져오기 실패: {e}'
            break

    ws.close()

    if value is not None:
        return jsonify({'value': value})
    else:
        return jsonify({'error': '변수를 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
