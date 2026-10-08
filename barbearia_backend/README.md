# Barbearia Vintage & Co. — Backend

Este projeto é o backend de um protótipo comercial de site com painel administrativo para a barbearia fictícia **Barbearia Vintage & Co.**

O sistema permite:

- exibir informações públicas da barbearia;
- listar categorias, serviços, barbeiros e promoções;
- detalhar serviços;
- filtrar e pesquisar serviços;
- gerar um link de agendamento pelo WhatsApp;
- administrar o catálogo por um painel frontend separado.

Este backend **não** implementa agendamento com horários, calendário, checkout, pagamentos, carrinho, pedidos ou faturamento.

## Para o empresário

O sistema funciona como um catálogo digital.

O administrador entra no painel e pode:

- cadastrar ou editar categorias de serviços;
- cadastrar, editar, ocultar ou excluir serviços;
- cadastrar e editar barbeiros;
- cadastrar ou editar promoções;
- alterar o nome, slogan, endereço demonstrativo, horário, WhatsApp e banner da barbearia.

O site público mostra apenas o conteúdo publicado e ativo.

Por exemplo:

- um serviço oculto não aparece no site;
- um serviço vinculado a uma categoria inativa também não aparece;
- um barbeiro inativo não aparece;
- uma promoção fora do período não aparece;
- uma alteração feita no painel passa a ser visível na API pública.

Os dados iniciais são fictícios. Antes de publicar, substitua:

- nome;
- slogan;
- descrição;
- WhatsApp;
- endereço;
- horários;
- imagens;
- serviços;
- preços;
- promoções.

## Tecnologias

- Python 3.13
- Django 5.2
- Django REST Framework 3.16
- SQLite no desenvolvimento
- PostgreSQL preparado para produção
- Pillow para validação de imagens
- django-cors-headers para desenvolvimento local
- python-dotenv para variáveis de ambiente

## Estrutura do projeto

```text
barbearia_backend/
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
├── README.md
├── API_CONTRACT.md
├── barbearia_backend/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── catalog/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── management/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── seed_demo.py
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py
    ├── models.py
    ├── pagination.py
    ├── permissions.py
    ├── serializers.py
    ├── urls.py
    ├── validators.py
    ├── views.py
    └── tests/
        ├── __init__.py
        ├── test_public_api.py
        ├── test_admin_api.py
        ├── test_authentication.py
        ├── test_validations.py
        └── test_promotions.py
```

## Instalação local

### 1. Criar o ambiente virtual

A partir da pasta do projeto:

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install --requirement requirements.txt
```

### 3. Criar o arquivo de ambiente

No Windows:

```bash
copy .env.example .env
```

No Linux ou macOS:

```bash
cp .env.example .env
```

Abra o arquivo `.env` e altere a `SECRET_KEY`.

Para desenvolvimento local, os valores padrão são suficientes:

```env
DEBUG=True
SECRET_KEY=coloque-aqui-uma-chave-secreta-diferente
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=sqlite
```

Nunca publique o arquivo `.env`.

### 4. Aplicar migrações

```bash
python manage.py migrate
```

### 5. Criar dados demonstrativos

```bash
python manage.py seed_demo
```

O comando cria:

- configuração da Barbearia Vintage & Co.;
- três categorias;
- sete serviços;
- três barbeiros;
- uma promoção;
- dados fictícios;
- sem imagens externas;
- sem usuário administrador.

Você pode executar o comando mais de uma vez. Ele atualiza os registros em vez de criar duplicatas.

### 6. Criar o primeiro administrador

```bash
python manage.py createsuperuser
```

Informe:

```text
Username
Email
Password
```

A senha deve ser forte e privada. Ela não deve ser colocada no código, no README ou no `.env.example`.

O usuário criado terá `is_staff=True` e poderá fazer login no painel frontend.

### 7. Iniciar o servidor

```bash
python manage.py runserver
```

A API estará disponível em:

```text
http://127.0.0.1:8000/api/v1/
```

O Django Admin auxiliar estará em:

```text
http://127.0.0.1:8000/django-admin/
```

## Testar a API

### Dados da barbearia

```bash
curl http://127.0.0.1:8000/api/v1/public/store/
```

### Categorias

```bash
curl http://127.0.0.1:8000/api/v1/public/categories/
```

### Serviços

```bash
curl http://127.0.0.1:8000/api/v1/public/services/
```

### Buscar serviços

```bash
curl "http://127.0.0.1:8000/api/v1/public/services/?search=barba"
```

### Filtrar por categoria

```bash
curl "http://127.0.0.1:8000/api/v1/public/services/?category=cortes"
```

### Filtrar destaques

```bash
curl "http://127.0.0.1:8000/api/v1/public/services/?featured=true"
```

### Paginar serviços

```bash
curl "http://127.0.0.1:8000/api/v1/public/services/?page=1&page_size=12"
```

### Barbeiros

```bash
curl http://127.0.0.1:8000/api/v1/public/barbers/
```

### Promoções

```bash
curl http://127.0.0.1:8000/api/v1/public/promotions/
```

## Login administrativo

O painel frontend deve seguir esta ordem:

```text
1. GET  /api/v1/auth/csrf/
2. POST /api/v1/auth/login/
3. GET  /api/v1/auth/me/
4. Operações administrativas
5. POST /api/v1/auth/logout/
```

### Obter CSRF

```bash
curl -c cookies.txt http://127.0.0.1:8000/api/v1/auth/csrf/
```

### Fazer login

```bash
curl -b cookies.txt -c cookies.txt \
  -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TOKEN_DO_CSRF" \
  -d '{"username":"SEU_USUARIO","password":"SUA_SENHA"}'
```

Substitua:

- `TOKEN_DO_CSRF`;
- `SEU_USUARIO`;
- `SUA_SENHA`.

### Consultar usuário autenticado

```bash
curl -b cookies.txt http://127.0.0.1:8000/api/v1/auth/me/
```

### Encerrar sessão

```bash
curl -b cookies.txt -c cookies.txt \
  -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \
  -H "X-CSRFToken: TOKEN_DO_CSRF"
```

## Upload de imagem

Para criar um serviço com imagem, use `multipart/form-data`.

```bash
curl -b cookies.txt -c cookies.txt \
  -X POST http://127.0.0.1:8000/api/v1/admin/services/ \
  -H "X-CSRFToken: TOKEN_DO_CSRF" \
  -F "categoria=1" \
  -F "nome=Corte Demonstrativo" \
  -F "slug=corte-demonstrativo" \
  -F "descricao_curta=Corte fictício." \
  -F "descricao_completa=Descrição completa fictícia." \
  -F "preco=55.00" \
  -F "duracao_minutos=45" \
  -F "alt_text=Corte demonstrativo" \
  -F "status_published=true" \
  -F "imagem_principal=@./imagens/corte.jpg"
```

Formatos aceitos:

- JPEG;
- JPG;
- PNG;
- WebP.

O limite padrão é 5 MB.

A API valida o conteúdo real da imagem com Pillow. Não basta enviar um arquivo com extensão `.jpg`.

## Executar testes

```bash
python manage.py test catalog.tests
```

Não considere o projeto validado apenas por ter recebido os arquivos. Execute os testes no seu ambiente e corrija eventuais divergências.

## Frontend separado

O frontend deve consumir apenas a API REST.

O Django Admin:

```text
/django-admin/
```

é apenas uma ferramenta auxiliar. Ele não substitui o painel frontend.

As rotas do painel personalizado são:

```text
/api/v1/admin/
```

## Desenvolvimento com frontend separado

Se o frontend estiver em:

```text
http://localhost:3000
```

e o backend em:

```text
http://localhost:8000
```

configure no `.env` do backend:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
```

O frontend deve usar:

```javascript
credentials: "include"
```

E enviar o header:

```http
X-CSRFToken
```

em todas as requisições:

- `POST`;
- `PATCH`;
- `DELETE`.

Não armazene senha, token CSRF ou sessão no `localStorage`.

## Deploy em produção

Em produção, utilize:

```env
DEBUG=False
SECRET_KEY=chave-secreta-diferente
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
DB_ENGINE=postgresql
DB_DATABASE=barbearia_db
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_HOST=host_do_banco
DB_PORT=5432
SITE_URL=[https://seudominio.com](https://seudominio.com)
```

Em produção com HTTPS:

```env
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

### Migrações

```bash
python manage.py migrate
```

### Arquivos estáticos

```bash
python manage.py collectstatic
```

### Mídia

Não use `runserver` em produção.

Os arquivos enviados pelos administradores devem ser servidos por:

- Nginx;
- CDN;
- serviço de armazenamento;
- ou outro servidor de arquivos adequado.

### GitHub Actions

Crie:

```text
.github/workflows/tests.yml
```

Com um workflow básico:

```yaml
name: Testes do backend

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Instalar dependências
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Verificar projeto
        run: python manage.py check

      - name: Executar testes
        run: python manage.py test catalog.tests
```

## Avisos importantes

- Os dados do `seed_demo` são fictícios.
- O número de WhatsApp do seed não deve ser usado como contato real.
- O endereço é fictício.
- As imagens não são criadas pelo seed.
- Não publique o projeto com dados de demonstração sem substituí-los.
- Não versione o arquivo `.env`.
- Não crie credenciais administrativas públicas.
- Não desative CSRF para “fazer funcionar”.
- Não use `localStorage` para guardar credenciais.