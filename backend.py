import json
import os
import random
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from supabase import create_client
import openai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://kjmbobqfynkgmccpuepx.supabase.co/rest/v1/')
SUPABASE_URL = RAW_SUPABASE_URL.rstrip('/')
if SUPABASE_URL.endswith('/rest/v1'):
    SUPABASE_URL = SUPABASE_URL[: -len('/rest/v1')]
SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbWJvYnFmeW5rZ21jY3B1ZXB4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1NjQxNzUsImV4cCI6MjA5MzE0MDE3NX0.6IpdaoUg2B-h9TdSqLct77UKG4Vpu2fY77DLSbXHCDI'
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
USE_LOCAL_FALLBACK = os.environ.get('USE_LOCAL_FALLBACK', '1').lower() in ('1', 'true', 'yes')
openai.api_key = OPENAI_API_KEY

def generate_local_ad(prompt, style):
    titles = [
        f'{style} para {prompt}',
        f'{style} com foco em {prompt}',
        f'{prompt} no estilo {style}',
        f'{style} que destaca {prompt}'
    ]
    actions = ['compre agora', 'saiba mais', 'experimente hoje', 'veja já']
    benefits = [
        'aumente suas vendas',
        'chame mais atenção',
        'valorize sua marca',
        'conquiste novos clientes'
    ]
    title = random.choice(titles)
    description = (
        f'Anúncio gerado localmente: destaque {benefits[random.randrange(len(benefits))]}, '
        f'use linguagem clara e um convite para {random.choice(actions)}. '
        f'Foque em {prompt} para atrair seu público no estilo {style}.'
    )
    return title, description

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

    if not OPENAI_API_KEY:
        if USE_LOCAL_FALLBACK:
            title, description = generate_local_ad(prompt, style)
            return jsonify({'result': {'title': title, 'description': description}})
        return jsonify({'message': 'OPENAI_API_KEY não configurada. Defina a variável de ambiente OPENAI_API_KEY.'}), 500

    try:
        response = openai.ChatCompletion.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Você é um assistente especialista em copywriting para anúncios online. '
                        'Gere um título curto e persuasivo e uma descrição que destaque benefícios, valor e um chamado à ação claro.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Crie um anúncio para: "{prompt}" no estilo "{style}". '
                        'Retorne apenas JSON válido com os campos title e description.'
                    )
                }
            ],
            max_tokens=200,
            temperature=0.8,
        )
        content = response.choices[0].message.content.strip()
        try:
            result_data = json.loads(content)
            title = result_data.get('title', '').strip()
            description = result_data.get('description', '').strip()
        except Exception:
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            title = lines[0] if lines else f'{style} para {prompt}'
            description = ' '.join(lines[1:]) if len(lines) > 1 else content

        if not title or not description:
            raise ValueError('Resposta inválida do modelo de IA.')

        return jsonify({'result': {'title': title, 'description': description}})
    except Exception as error:
        return jsonify({'message': str(error)}), 500


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(BASE_DIR, path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
