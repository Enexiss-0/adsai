# AdsAI

Site e backend de micro SaaS para geração de anúncios com IA.

## Estrutura

- `index.html` — frontend da aplicação
- `styles.css` — estilos visuais
- `app.js` — lógica do frontend e chamadas à API
- `backend.py` — servidor Flask para autenticação JWT e geração de anúncios
- `requirements.txt` — dependências Python
- `users.json` — base simples de usuários (local)
- `Dockerfile` — contêiner pronto para deploy

## Rodar localmente

1. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

2. Defina sua chave de API OpenAI (opcional):

```powershell
$env:OPENAI_API_KEY = "sua_chave_openai"
```

Se você quiser testar sem chave OpenAI, deixe `OPENAI_API_KEY` vazio. O backend usa um gerador local simples para permitir testes gratuitos.

3. Inicie o backend:

```powershell
python backend.py
```

3. Abra no navegador:

```
http://127.0.0.1:5000
```

## Deploy online

### Opção 1: Docker

1. Construa a imagem:

```powershell
docker build -t adsai-saas .
```

2. Execute o container:

```powershell
docker run -p 5000:5000 adsai-saas
```

A aplicação ficará disponível em `http://localhost:5000`.

### Opção 2: Render

1. Crie um repositório no GitHub com este projeto.
2. No Render, crie um novo `Web Service` e conecte ao repositório.
3. Configure:
   - Build Command: `python -m pip install -r requirements.txt`
   - Start Command: `python backend.py`
   - Port: `5000`
4. Faça deploy.

### Opção 3: Railway

1. Conecte seu repositório ao Railway.
2. Configure o comando de start:

```text
python backend.py
```

3. O Railway irá expor a URL pública automaticamente.

## Observações

- O JWT já está implementado no backend e usado pelo frontend para autenticação.
- `users.json` armazena os usuários localmente no servidor.
- Para produção, você pode trocar `backend.py` por um servidor WSGI como `gunicorn` e usar um banco de dados real.
