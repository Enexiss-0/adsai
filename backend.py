import json
import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import jwt
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
JWT_SECRET = os.environ.get('JWT_SECRET', 'adsai-secret-token')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRES = timedelta(hours=5)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)


def read_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def create_token(payload):
    exp = datetime.utcnow() + JWT_EXPIRES
    token = jwt.encode({**payload, 'exp': exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return data
    except jwt.PyJWTError:
        return None


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/register', methods=['POST'])
def register():
    body = request.get_json() or {}
    name = body.get('name', '').strip()
    email = body.get('email', '').strip().lower()
    password = body.get('password', '').strip()

    if not name or not email or not password:
        return jsonify({'message': 'Nome, email e senha são obrigatórios.'}), 400

    users = read_users()
    if any(user['email'] == email for user in users):
        return jsonify({'message': 'Já existe uma conta com esse email.'}), 409

    hashed = generate_password_hash(password)
    user = {
        'id': str(int(datetime.utcnow().timestamp() * 1000)),
        'name': name,
        'email': email,
        'password': hashed,
        'createdAt': datetime.utcnow().isoformat() + 'Z'
    }
    users.append(user)
    write_users(users)

    token = create_token({'id': user['id'], 'email': user['email']})
    return jsonify({'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}, 'token': token}), 201


@app.route('/api/login', methods=['POST'])
def login():
    body = request.get_json() or {}
    email = body.get('email', '').strip().lower()
    password = body.get('password', '').strip()

    if not email or not password:
        return jsonify({'message': 'Email e senha são obrigatórios.'}), 400

    users = read_users()
    user = next((u for u in users if u['email'] == email), None)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Email ou senha inválidos.'}), 401

    token = create_token({'id': user['id'], 'email': user['email']})
    return jsonify({'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}, 'token': token})


@app.route('/api/profile', methods=['GET'])
def profile():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else None
    payload = verify_token(token)
    if not payload:
        return jsonify({'message': 'Token inválido ou expirado.'}), 401

    users = read_users()
    user = next((u for u in users if u['id'] == payload.get('id')), None)
    if not user:
        return jsonify({'message': 'Usuário não encontrado.'}), 404

    return jsonify({'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}})


@app.route('/api/generate', methods=['POST'])
def generate_ad():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else None
    payload = verify_token(token)
    if not payload:
        return jsonify({'message': 'Token inválido ou expirado.'}), 401

    body = request.get_json() or {}
    prompt = body.get('prompt', '').strip()
    style = body.get('style', '').strip()
    if not prompt or not style:
        return jsonify({'message': 'Prompt e estilo são obrigatórios.'}), 400

    title = f'{style} para {prompt}'
    description = 'Anúncio com foco em conversão: destaque o benefício principal, use uma chamada simples e convide o usuário a agir agora.'
    return jsonify({'result': {'title': title, 'description': description}})


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(BASE_DIR, path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
