# Barbearia Vintage & Co. — Frontend

SPA em **Vanilla JS + Vite** que consome o backend Django (DRF) da Barbearia Vintage & Co.
Inclui o site público e o painel administrativo, com login por sessão Django e CSRF.

## Requisitos

- Node.js 18 ou superior
- Backend Django em execução (padrão: `http://localhost:8000`)
- Pillow instalado no backend (validação de imagens)

## Instalação e execução

```bash
cd frontend
npm install
cp .env.example .env      # no Windows: copy .env.example .env
npm run dev
```

Abra `http://localhost:5173`.

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento com proxy para o Django |
| `npm run build` | Gera a versão de produção em `dist/` |
| `npm run preview` | Serve a pasta `dist/` localmente para conferência |

## Conectar ao backend Django

### Modo recomendado em desenvolvimento: proxy do Vite

Deixe `VITE_API_BASE_URL` **vazio** no `.env`. O Vite encaminha `/api` e `/media` para
`VITE_PROXY_TARGET` (padrão `http://localhost:8000`). Navegador, cookies e CSRF ficam na
mesma origem (`localhost:5173`), então **não é preciso configurar CORS**.

No backend:

```bash
cd barbearia_backend
python manage.py migrate
python manage.py createsuperuser     # o usuário precisa ter is_staff=True
python manage.py runserver           # porta 8000
```

Se o projeto não tiver comando de dados iniciais, cadastre a barbearia, categorias,
serviços e barbeiros pelo próprio painel (`/painel`).

### Modo direto (sem proxy)

Defina no `.env` do frontend:
