import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from supabase import create_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://kjmbobqfynkgmccpuepx.supabase.co/rest/v1/')
SUPABASE_URL = RAW_SUPABASE_URL.rstrip('/')
if SUPABASE_URL.endswith('/rest/v1'):
    SUPABASE_URL = SUPABASE_URL[: -len('/rest/v1')]
SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbWJvYnFmeW5rZ21jY3B1ZXB4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1NjQxNzUsImV4cCI6MjA5MzE0MDE3NX0.6IpdaoUg2B-h9TdSqLct77UKG4Vpu2fY77DLSbXHCDI'

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_from_token(token):
    if not token:
        return None

    user_response = supabase.auth.get_user(token)
    if not user_response:
        return None

    return user_response.user


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

    try:
        auth_response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {'name': name}
            }
        })
    except Exception as error:
        return jsonify({'message': str(error)}), 500

    if not auth_response or not auth_response.user:
        return jsonify({'message': 'Não foi possível criar a conta.'}), 500

    user = auth_response.user
    if not getattr(auth_response, 'session', None) or not getattr(auth_response.session, 'access_token', None):
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.user_metadata.get('name', ''),
                'email': user.email,
            },
            'confirm_required': True,
            'message': 'Conta criada. Verifique seu email para confirmar o acesso.',
        }), 202

    token = auth_response.session.access_token
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.user_metadata.get('name', ''),
            'email': user.email,
        },
        'token': token,
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    body = request.get_json() or {}
    email = body.get('email', '').strip().lower()
    password = body.get('password', '').strip()

    if not email or not password:
        return jsonify({'message': 'Email e senha são obrigatórios.'}), 400

    try:
        auth_response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })
    except Exception as error:
        return jsonify({'message': str(error)}), 500

    if not auth_response or not auth_response.session or not auth_response.user:
        return jsonify({'message': 'Email ou senha inválidos.'}), 401

    user = auth_response.user
    token = auth_response.session.access_token
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.user_metadata.get('name', ''),
            'email': user.email,
        },
        'token': token,
    })


@app.route('/api/profile', methods=['GET'])
def profile():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else None
    user = get_user_from_token(token)
    if not user:
        return jsonify({'message': 'Token inválido ou expirado.'}), 401

    return jsonify({'user': {'id': user.id, 'name': user.user_metadata.get('name', ''), 'email': user.email}})


@app.route('/api/generate', methods=['POST'])
def generate_ad():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else None
    user = get_user_from_token(token)
    if not user:
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
