# Barbearia Vintage & Co. — Contrato da API v1

Este documento descreve a API REST do backend para implementação do site público e do painel administrativo em frontend separado.

## Base da API

- Prefixo: `/api/v1/`
- Formato de resposta: JSON
- Banco local: SQLite
- Banco de produção: PostgreSQL
- Autenticação administrativa: sessão Django
- Proteção: CSRF
- Permissão administrativa: `is_staff=True`

Em desenvolvimento, a API é assumida em:

```text
http://localhost:8000
```

## Escopo

A API oferece:

- dados públicos da barbearia;
- categorias;
- serviços;
- barbeiros;
- promoções;
- autenticação administrativa;
- dashboard;
- CRUD administrativo;
- upload de imagens.

A API não oferece:

- agendamento com horário;
- calendário;
- checkout;
- pagamentos;
- carrinho;
- pedidos;
- faturamento;
- métricas de vendas;
- cadastro público de administradores.

## Endpoints públicos

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/public/store/` | Dados públicos da barbearia |
| GET | `/api/v1/public/categories/` | Categorias ativas |
| GET | `/api/v1/public/services/` | Serviços publicados (paginado) |
| GET | `/api/v1/public/services/<slug>/` | Detalhe de serviço publicado |
| GET | `/api/v1/public/barbers/` | Barbeiros ativos |
| GET | `/api/v1/public/barbers/<slug>/` | Detalhe de barbeiro ativo |
| GET | `/api/v1/public/promotions/` | Promoções elegíveis |

## Endpoints de autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/auth/csrf/` | Obtém token CSRF |
| POST | `/api/v1/auth/login/` | Faz login administrativo |
| GET | `/api/v1/auth/me/` | Retorna usuário autenticado |
| POST | `/api/v1/auth/logout/` | Encerra sessão |

## Endpoints administrativos

Todos exigem usuário autenticado com `is_staff=True`.

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/admin/dashboard/` | Contagens do catálogo |
| GET, POST | `/api/v1/admin/services/` | Lista e cria serviços (paginado) |
| GET, PATCH, DELETE | `/api/v1/admin/services/<id>/` | Detalhe, edição e exclusão |
| GET, POST | `/api/v1/admin/categories/` | Lista e cria categorias (paginado) |
| GET, PATCH, DELETE | `/api/v1/admin/categories/<id>/` | Detalhe, edição e exclusão |
| GET, POST | `/api/v1/admin/barbers/` | Lista e cria barbeiros (paginado) |
| GET, PATCH, DELETE | `/api/v1/admin/barbers/<id>/` | Detalhe, edição e exclusão |
| GET, PATCH | `/api/v1/admin/store/` | Consulta e edita configuração |
| GET, POST | `/api/v1/admin/promotions/` | Lista e cria promoções (paginado) |
| GET, PATCH, DELETE | `/api/v1/admin/promotions/<id>/` | Detalhe, edição e exclusão |

## Regras públicas

### Serviços

Um serviço aparece publicamente somente quando:

```text
status_published = true
e categoria.ativa = true
```

### Categorias

Somente categorias com:

```text
ativa = true
```

aparecem publicamente.

### Barbeiros

Somente barbeiros com:

```text
ativo = true
```

aparecem publicamente.

### Promoções

Uma promoção aparece publicamente quando:

```text
ativa = true
e data_inicio é nula ou já alcançada
e data_fim é nula ou ainda não ultrapassada
e serviço vinculado é nulo ou publicado em categoria ativa
```

## Filtros de serviços

```http
GET /api/v1/public/services/
```

Parâmetros aceitos:

| Parâmetro | Valor |
|---|---|
| `search` | Texto pesquisado em `nome` e `descricao_curta` |
| `category` | Slug da categoria |
| `featured` | Apenas `true` (case-insensitive) |
| `page` | Número da página |
| `page_size` | Quantidade por página |
| `ordering` | `name`, `-name`, `price` ou `-price` |

Exemplo:

```text
/api/v1/public/services/?search=barba&category=barba&featured=true&page=1&page_size=12
```

### Comportamento do filtro `featured`

- `featured=true` ou `featured=True`: retorna apenas serviços com `destaque_pagina_inicial = true`;
- `featured=false`, `featured=1`, `featured=yes`: retorna erro 400;
- parâmetro omitido: retorna todos os serviços publicados.

### Ordenação

Quando `ordering` não é enviado, a ordenação padrão é:

```text
display_order, name, id
```

Quando enviado, os valores aceitos são:

```text
name      (nome ascendente)
-name     (nome descendente)
price     (preço ascendente)
-price    (preço descendente)
```

## Paginação

As listagens paginadas retornam:

```json
{
  "count": 7,
  "next": null,
  "previous": null,
  "results": []
}
```

Configuração:

```text
page_size padrão: 12
page_size máximo: 50
```

Endpoints paginados:

- `/api/v1/public/services/`
- `/api/v1/admin/services/`
- `/api/v1/admin/categories/`
- `/api/v1/admin/barbers/`
- `/api/v1/admin/promotions/`

## Campos JSON públicos

### Store

```json
{
  "nome_da_barbearia": "Barbearia Vintage & Co.",
  "slogan": "Estilo clássico, cuidado contemporâneo.",
  "descricao_apresentacao": "Descrição fictícia.",
  "numero_whatsapp": "5521999999999",
  "endereco_demo": "Endereço fictício.",
  "horario_atendimento": "Horário fictício.",
  "imagem_capa_banner": null,
  "texto_banner": "Texto do banner.",
  "texto_botao_principal": "Agendar pelo WhatsApp"
}
```

Resposta 404 quando a configuração não existe:

```json
{
  "detail": "As informações da barbearia ainda não foram configuradas."
}
```

### Categoria

```json
{
  "id": 1,
  "nome": "Cortes",
  "slug": "cortes",
  "descricao_curta": "Cortes clássicos e modernos.",
  "ordem_exibicao": 1
}
```

### Serviço em listagem

```json
{
  "id": 1,
  "categoria": {
    "id": 1,
    "nome": "Cortes",
    "slug": "cortes",
    "descricao_curta": "Cortes clássicos e modernos.",
    "ordem_exibicao": 1
  },
  "nome": "Corte Vintage",
  "slug": "corte-vintage",
  "descricao_curta": "Corte clássico com acabamento moderno.",
  "preco": "55.00",
  "duracao_minutos": 45,
  "imagem_principal": "/media/services/uuid.jpg",
  "alt_text": "Corte Vintage masculino",
  "destaque_pagina_inicial": true,
  "status_published": true,
  "ordem_exibicao": 1
}
```

### Serviço em detalhe

O detalhe inclui todos os campos da listagem, mais:

```json
{
  "descricao_completa": "Descrição completa do serviço."
}
```

### Barbeiro em listagem

```json
{
  "id": 1,
  "nome": "Arthur Valença",
  "slug": "arthur-valenca",
  "especialidade": "Cortes clássicos",
  "descricao_curta": "Barbeiro fictício.",
  "foto_principal": "/media/barbers/uuid.jpg",
  "alt_text": "Foto fictícia",
  "ordem_exibicao": 1,
  "ativo": true
}
```

### Barbeiro em detalhe

O detalhe inclui todos os campos da listagem, mais:

```json
{
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

### Promoção

```json
{
  "id": 1,
  "titulo": "Promoção fictícia",
  "descricao": "Descrição fictícia.",
  "imagem": "/media/promotions/uuid.jpg",
  "servico_vinculado": {
    "id": 1,
    "categoria": {
      "id": 1,
      "nome": "Barba",
      "slug": "barba",
      "descricao_curta": "Serviços de barba.",
      "ordem_exibicao": 1
    },
    "nome": "Barba Premium",
    "slug": "barba-premium",
    "descricao_curta": "Experiência completa.",
    "preco": "60.00",
    "duracao_minutos": 45,
    "imagem_principal": "/media/services/uuid.jpg",
    "alt_text": "Barba Premium",
    "destaque_pagina_inicial": true,
    "status_published": true,
    "ordem_exibicao": 1
  },
  "data_inicio": "2026-10-04T20:00:00Z",
  "data_fim": "2027-10-04T20:00:00Z",
  "ativa": true,
  "ordem_exibicao": 1
}
```

## Campos JSON administrativos

### Categoria

```json
{
  "id": 1,
  "nome": "Cortes",
  "slug": "cortes",
  "descricao_curta": "Cortes clássicos.",
  "ordem_exibicao": 1,
  "ativa": true,
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

### Serviço

```json
{
  "id": 1,
  "categoria": 1,
  "nome": "Corte Vintage",
  "slug": "corte-vintage",
  "descricao_curta": "Corte clássico.",
  "descricao_completa": "Descrição completa.",
  "preco": "55.00",
  "duracao_minutos": 45,
  "imagem_principal": "/media/services/uuid.jpg",
  "alt_text": "Corte Vintage",
  "destaque_pagina_inicial": true,
  "status_published": true,
  "ordem_exibicao": 1,
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

### Barbeiro

```json
{
  "id": 1,
  "nome": "Arthur Valença",
  "slug": "arthur-valenca",
  "especialidade": "Cortes clássicos",
  "descricao_curta": "Barbeiro fictício.",
  "foto_principal": "/media/barbers/uuid.jpg",
  "alt_text": "Foto fictícia",
  "ordem_exibicao": 1,
  "ativo": true,
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

### Store

```json
{
  "id": 1,
  "nome_da_barbearia": "Barbearia Vintage & Co.",
  "slogan": "Estilo clássico.",
  "descricao_apresentacao": "Descrição fictícia.",
  "numero_whatsapp": "5521999999999",
  "endereco_demo": "Endereço fictício.",
  "horario_atendimento": "Horário fictício.",
  "imagem_capa_banner": "/media/store/uuid.jpg",
  "texto_banner": "Texto fictício.",
  "texto_botao_principal": "Agendar pelo WhatsApp",
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

### Promoção

```json
{
  "id": 1,
  "titulo": "Promoção fictícia",
  "descricao": "Descrição fictícia.",
  "imagem": "/media/promotions/uuid.jpg",
  "servico_vinculado": 1,
  "data_inicio": "2026-10-04T20:00:00Z",
  "data_fim": "2027-10-04T20:00:00Z",
  "ativa": true,
  "ordem_exibicao": 1,
  "data_criacao": "2026-10-04T20:00:00Z",
  "data_atualizacao": "2026-10-04T20:00:00Z"
}
```

## Slug

Em serviços, categorias e barbeiros, o campo `slug` é opcional na criação.

- Se não for enviado, o backend gera o slug a partir de `nome`, em minúsculas e sem acentos.
- Se já existir, é acrescentado um sufixo numérico (`-2`, `-3`...).
- Se for enviado e já existir, a API retorna `400` com erro no campo `slug`.
- Na edição (`PATCH`), o slug não é alterado automaticamente.

## Dashboard

```http
GET /api/v1/admin/dashboard/
```

Resposta:

```json
{
  "services_count": 7,
  "categories_count": 3,
  "barbers_count": 3,
  "active_promotions_count": 1
}
```

Não existem métricas de vendas, faturamento, acessos ou agendamentos.

## CSRF e sessão

### 1. Obter CSRF

```http
GET /api/v1/auth/csrf/
```

Resposta:

```json
{
  "csrfToken": "token-gerado"
}
```

O navegador também recebe o cookie:

```text
csrftoken
```

### 2. Login

```http
POST /api/v1/auth/login/
Content-Type: application/json
X-CSRFToken: token-gerado
Cookie: csrftoken=token-gerado
```

Corpo:

```json
{
  "username": "usuario_criado_manualmente",
  "password": "senha_privada"
}
```

Resposta 200:

```json
{
  "user": {
    "id": 1,
    "username": "usuario_criado_manualmente",
    "is_staff": true
  },
  "csrfToken": "novo-token"
}
```

Resposta 400 (campos inválidos):

```json
{
  "detail": "Informe username e password como textos."
}
```

Resposta 403 (credenciais inválidas ou usuário não staff):

```json
{
  "detail": "Credenciais inválidas ou acesso administrativo não autorizado."
}
```

### 3. Requisições administrativas

O frontend deve usar:

```javascript
credentials: "include"
```

Nas escritas, deve enviar:

```http
X-CSRFToken: novo-token
```

Métodos protegidos:

```text
POST
PATCH
DELETE
```

### 4. Logout

```http
POST /api/v1/auth/logout/
X-CSRFToken: novo-token
Cookie: csrftoken=novo-token
```

Resposta 204: Sem corpo.

Resposta 403: Usuário não autenticado.

## Uploads

Para enviar imagem, use `multipart/form-data`.

| Recurso | Campo |
|---|---|
| Serviço | `imagem_principal` |
| Barbeiro | `foto_principal` |
| Store | `imagem_capa_banner` |
| Promoção | `imagem` |

Formatos aceitos:

```text
JPEG
JPG
PNG
WebP
```

Limite padrão:

```text
5 MB
```

O backend valida o conteúdo real da imagem com Pillow.

Os nomes dos arquivos são gerados com UUID:

```text
/media/services/uuid.jpg
/media/barbers/uuid.jpg
/media/store/uuid.jpg
/media/promotions/uuid.jpg
```

As URLs retornadas podem ser:

- relativas, por exemplo `/media/services/uuid.jpg`;
- absolutas, dependendo da configuração `MEDIA_URL` e do contexto da requisição.

O frontend deve aceitar ambos os formatos.

### Envio de formulários com upload

Quando houver upload de imagem:

- use `FormData`;
- não defina manualmente o header `Content-Type`;
- envie booleanos como strings, por exemplo `"true"` ou `"false"`;
- envie números decimais como strings, por exemplo `"55.00"`.

Exemplo de criação de serviço com imagem:

```javascript
const formData = new FormData();
formData.append("categoria", "1");
formData.append("nome", "Corte Degradê");
formData.append("descricao_curta", "Corte moderno...");
formData.append("descricao_completa", "Descrição completa...");
formData.append("preco", "55.00");
formData.append("duracao_minutos", "40");
formData.append("imagem_principal", arquivoImagem);
formData.append("alt_text", "Corte degradê");
formData.append("destaque_pagina_inicial", "true");
formData.append("status_published", "true");
formData.append("ordem_exibicao", "3");
```

## Campos obrigatórios na criação

### Serviço

Obrigatórios:

```text
categoria
nome
descricao_curta
descricao_completa
preco
duracao_minutos
```

Opcionais:

```text
slug
imagem_principal
alt_text
destaque_pagina_inicial
status_published
ordem_exibicao
```

### Categoria

Obrigatório:

```text
nome
```

Opcionais:

```text
slug
descricao_curta
ordem_exibicao
ativa
```

### Barbeiro

Obrigatórios:

```text
nome
especialidade
descricao_curta
```

Opcionais:

```text
slug
foto_principal
alt_text
ordem_exibicao
ativo
```

### Promoção

Obrigatórios apenas na criação:

```text
titulo
descricao
```

Opcionais:

```text
imagem
servico_vinculado
data_inicio
data_fim
ativa
ordem_exibicao
```

Na edição (`PATCH`), `titulo` e `descricao` tornam-se opcionais.

### Store

Na atualização de registro existente (`PATCH`), todos os campos são opcionais.

Na criação automática (quando o registro não existe), os campos obrigatórios do modelo devem ser enviados:

```text
nome_da_barbearia
slogan
descricao_apresentacao
numero_whatsapp
endereco_demo
horario_atendimento
texto_banner
```

## Códigos HTTP

| Situação | Código |
|---|---:|
| Consulta bem-sucedida | 200 |
| Criação bem-sucedida | 201 |
| Atualização bem-sucedida | 200 |
| Exclusão bem-sucedida | 204 |
| Logout bem-sucedido | 204 |
| Erro de validação | 400 |
| Acesso administrativo negado | 403 |
| Registro inexistente | 404 |
| Categoria com serviços | 409 |

### Acesso administrativo (403)

O backend utiliza `403` para:

- usuário anônimo em endpoint administrativo;
- usuário autenticado sem `is_staff=True`;
- credenciais inválidas no login;
- sessão expirada em `/api/v1/auth/me/`.

Não espere `401` nesta API.

## Exemplos de erro

### Preço negativo

```json
{
  "preco": [
    "O preço não pode ser negativo."
  ]
}
```

### Duração inválida

```json
{
  "duracao_minutos": [
    "A duração deve ser maior que zero minuto."
  ]
}
```

### Imagem inválida

```json
{
  "imagem_principal": [
    "O arquivo enviado não é uma imagem válida."
  ]
}
```

### Promoção com período inválido

```json
{
  "data_fim": [
    "A data final não pode ser anterior à data inicial."
  ]
}
```

### Categoria com serviços

```json
{
  "detail": "Não é possível excluir uma categoria que possui serviços vinculados."
}
```

### Acesso administrativo negado

```json
{
  "detail": "É necessário estar autenticado como administrador para acessar este recurso."
}
```

### Parâmetro `featured` inválido

```json
{
  "featured": [
    "Utilize featured=true ou omita este parâmetro."
  ]
}
```

### Parâmetro `ordering` inválido

```json
{
  "ordering": [
    "Utilize name, -name, price ou -price."
  ]
}
```

## Regras de exclusão

### Categoria

- categoria com serviços vinculados não pode ser excluída;
- retorna `409` com mensagem explicativa;
- serviços devem ser excluídos ou movidos para outra categoria antes.

### Serviço

- pode ser excluído livremente;
- promoções vinculadas recebem `servico_vinculado: null` (comportamento `SET_NULL`).

### Barbeiro

- pode ser excluído livremente;
- não há dependências registradas.

### Promoção

- pode ser excluída livremente;
- não afeta o serviço vinculado.

## Regras para o frontend

- Use `credentials: "include"` em todas as chamadas.
- Obtenha o CSRF antes do login.
- Substitua o token CSRF pelo valor retornado no login.
- Envie `X-CSRFToken` em `POST`, `PATCH` e `DELETE`.
- Não use `localStorage` para senha, sessão ou token.
- Não confie no frontend para proteger rotas administrativas.
- Use preço como string decimal.
- Trate imagens ausentes como `null`.
- Não insira textos da API diretamente como HTML.
- Não ative link de WhatsApp com o número fictício do seed.
- Considere todos os dados do seed como demonstrativos.
- Aceite URLs de imagem relativas ou absolutas.
- Espere `403` para acesso negado, não `401`.

## Observações sobre a implementação real

### Permissão no logout

A view de logout utiliza `IsAuthenticated` em vez de `IsStaffAuthenticated`. Isso significa que, tecnicamente, um usuário autenticado não-staff pode acessar o endpoint de logout. O comportamento pretendido é que apenas administradores utilizem o painel, mas a implementação atual permite que qualquer usuário autenticado encerre sua sessão.

### URLs de imagem

As URLs de imagem retornadas dependem da configuração `MEDIA_URL` e do contexto da requisição. Em desenvolvimento local, é comum receber caminhos relativos como `/media/services/uuid.jpg`. Em produção, com configuração adequada, podem ser retornadas URLs absolutas. O frontend deve lidar com ambos os casos.

### Validação de imagens

O backend valida:

- tipo de arquivo (JPEG, PNG, WebP);
- conteúdo real da imagem usando Pillow;
- tamanho máximo configurado (atualmente 5 MB).

Arquivos corrompidos ou com extensão enganosa são rejeitados.