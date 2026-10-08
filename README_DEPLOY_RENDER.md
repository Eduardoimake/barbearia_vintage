# Deploy da Barbearia Vintage & Co. no Render

## 1. Pré-requisitos
- Conta no GitHub e repositório com este projeto (backend e frontend juntos).
- Conta no Render.
- Python 3.13 e Node 22 (versões usadas no Blueprint).
- **Armazenamento de mídia (obrigatório):** este projeto usa armazenamento S3 compatível
  (recomendado: Cloudflare R2). Motivo: o Render só oferece Persistent Disk em serviços pagos;
  Web Services Free têm sistema de arquivos efêmero e perdem uploads a cada deploy.
  Passo a passo (R2):
  1. Crie um bucket (ex.: `barbearia-media`).
  2. Habilite acesso público (domínio `r2.dev` ou domínio próprio) → será o `AWS_S3_CUSTOM_DOMAIN`.
  3. Crie um token de API S3 com permissão de leitura/escrita no bucket → `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`.
  4. Endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`; região: `auto`.
- Alternativa (plano pago): Persistent Disk. Use `MEDIA_STORAGE=local`, `MEDIA_ROOT=/var/data/media`
  e adicione ao serviço no `render.yaml` um bloco `disk` (`name`, `mountPath: /var/data`, `sizeGB`).
  Serviços com disco não fazem deploy sem interrupção e não escalam para várias instâncias.

## 2. Desenvolvimento local
### Backend
```bash
cd barbearia_backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py test
python manage.py createsuperuser
python manage.py runserver
```
SQLite é o padrão. Para PostgreSQL local: `DATABASE_URL=postgresql://usuario:senha@localhost:5432/barbearia_db`
ou as variáveis `DB_ENGINE=postgresql` + `DB_*`.
### Frontend
```bash
cd barbearia_frontend
npm ci
cp .env.example .env     # VITE_API_BASE_URL vazio = usa o proxy do Vite
npm run dev              # http://localhost:5173
npm run build
```
Variáveis `VITE_*` ficam visíveis no bundle final: nunca coloque segredos nelas.

## 3. Deploy pelo Blueprint
1. Faça commit e push de todos os arquivos (incluindo `render.yaml`).
2. Abra o Render → **Blueprints** → **New Blueprint Instance**.
3. Selecione o repositório e aplique o `render.yaml`.
4. Preencha as variáveis `sync: false`:
   - `AWS_*` (mídia) conforme a seção 1;
   - `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`: ainda não há URLs reais;
     coloque valores provisórios (ex.: `localhost`, `https://exemplo.onrender.com`) e corrija no passo 8;
   - `VITE_API_BASE_URL`: provisório (ex.: `https://exemplo.onrender.com`).
5. Aguarde o deploy do backend (build: dependências → check → collectstatic → migrate).
6. Copie a URL do backend (ex.: `https://barbearia-api.onrender.com`).
7. No Static Site, defina `VITE_API_BASE_URL` com essa URL, **sem barra final**.
   Ela é lida durante o build do Vite: alterar exige **novo deploy do Static Site** (Manual Deploy).
8. No backend, atualize (apenas hosts/origens, sem caminho e sem barra final):
   - `ALLOWED_HOSTS=barbearia-api.onrender.com`
   - `CORS_ALLOWED_ORIGINS=https://barbearia-frontend.onrender.com`
   - `CSRF_TRUSTED_ORIGINS=https://barbearia-frontend.onrender.com`
   - `SITE_URL=https://barbearia-api.onrender.com`
   O backend reinicia ao salvar.
9. Verifique `/health/`, `/api/v1/public/store/` e a home do frontend.

## 4. Criar o administrador
O build **não** cria superusuário. O plano Free do Render **não** tem shell nem jobs avulsos.
- **Opção A (Free ou qualquer plano):** no painel do banco, copie a *External Database URL*; no seu computador:
  ```bash
  cd barbearia_backend && source .venv/bin/activate
  export DATABASE_URL='<external-url>'   # só nesta sessão; nunca em arquivo versionado
  export DEBUG=true SECRET_KEY=qualquer-valor-local
  python manage.py createsuperuser
  unset DATABASE_URL
  ```
  Depois, se possível, restrinja o *IP allow list* do banco.
- **Opção B (plano pago):** use o Shell do Render no Web Service e rode `python manage.py createsuperuser`.
- O primeiro `PATCH /api/v1/admin/store/` (tela "Barbearia" do painel) cria a configuração única.

## 5. Checklist de aceitação
- [ ] `GET https://API/health/` → 200 `{"status":"ok"}`.
- [ ] `GET /api/v1/public/categories/`, `/public/services/`, `/public/barbers/`, `/public/promotions/` → 200.
- [ ] Home carrega sem erros no console (aba Network sem CORS/401 inesperado).
- [ ] Abrir direto `https://FRONT/painel/login` e `https://FRONT/servicos`; atualizar a página (F5) → sem 404.
- [ ] Login em `/painel/login` (cookies `sessionid` e `csrftoken` com `Secure; SameSite=None`).
- [ ] CRUD de categorias, serviços, barbeiros, promoções e configurações da barbearia.
- [ ] Upload de imagem; a URL da imagem abre em aba anônima.
- [ ] Fazer novo deploy do backend e confirmar que a imagem continua acessível.
- [ ] Logout e acesso a `/painel` redireciona ao login.
- [ ] `https://API/django-admin/` abre com CSS e permite login.
- [ ] Logs do Render sem erros 500.

Erros comuns:
- `DisallowedHost`: ajuste `ALLOWED_HOSTS`.
- CSRF 403: confira `CSRF_TRUSTED_ORIGINS` (https, sem barra).
- Erro de CORS: confira `CORS_ALLOWED_ORIGINS` exato.
- Login "funciona" mas `/auth/me/` dá 401: o navegador bloqueou cookies de terceiros (ver limitações).
- `ImproperlyConfigured`: a mensagem diz qual variável falta.
- Frontend chamando URL antiga: refaça o deploy do Static Site.

## 6. Domínio próprio
Atualize no backend `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` e `SITE_URL`
com os novos domínios HTTPS e, no frontend, `VITE_API_BASE_URL`.
**Mudar a URL da API exige rebuild/redeploy do frontend.**
Recomendação: use subdomínios do mesmo domínio (`www.seusite.com.br` e `api.seusite.com.br`);
assim os cookies passam a ser *same-site* e funcionam em todos os navegadores.

## 7. Limitações
- `*.onrender.com` está na Public Suffix List: front e API em URLs padrão do Render são *cross-site*.
  Chrome ainda aceita o cookie; Safari e Firefox/Brave com bloqueio estrito podem recusá-lo.
  A solução definitiva é o domínio próprio da seção 6.
- Plano Free: backend "dorme" após inatividade (primeira requisição lenta) e o PostgreSQL Free expira em 30 dias.
  Faça upgrade antes de operar para clientes reais.