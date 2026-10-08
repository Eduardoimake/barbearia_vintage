# Checklist manual — Roteiro comercial

Use um navegador limpo (ou janela anônima) e marque cada item.

## 0. Preparação

- [ ] Backend rodando em `http://localhost:8000` e frontend em `http://localhost:5173`.
- [ ] Existe um usuário com `is_staff=True` (criado com `createsuperuser`).
- [ ] Pillow instalado no backend.

## 1. Site público (visitante)

- [ ] `/` mostra hero, categorias, serviços em destaque, promoções, sobre nós, como funciona, contato e rodapé.
- [ ] Cada seção mostra "Carregando..." e depois o conteúdo, ou um estado vazio claro.
- [ ] O botão de WhatsApp aparece **desativado** enquanto o número for o demonstrativo.
- [ ] `/servicos`: a busca (ex.: "barba") filtra após uma breve pausa; o resumo "N serviços encontrados" é atualizado.
- [ ] O filtro de categoria e a ordenação (nome, preço) funcionam e ficam na URL.
- [ ] A paginação aparece quando há mais de 12 serviços; "Limpar filtros" restaura a lista.
- [ ] Clicar em um serviço abre `/servico/<slug>` com imagem, preço (ex.: R$ 55,00), duração e descrição completa.
- [ ] Um slug inexistente (`/servico/nao-existe`) mostra "Serviço não encontrado".
- [ ] `/equipe` lista apenas barbeiros ativos. `/contato` mostra endereço e horário.
- [ ] Uma rota inexistente (`/xyz`) mostra "Página não encontrada".

## 2. Login

- [ ] `/painel` sem sessão redireciona para `/painel/login?next=/painel`.
- [ ] Enviar o formulário vazio mostra erros por campo.
- [ ] Credenciais erradas mostram a mensagem do backend e o campo de senha é limpo.
- [ ] Um usuário que não é staff é recusado.
- [ ] Login correto leva ao `/painel` (ou ao destino de `next`) e exibe "Conectado como ...".
- [ ] DevTools > Application: `localStorage` e `sessionStorage` estão **vazios**.

## 3. Configuração da barbearia

- [ ] `/painel/barbearia`: com o número demonstrativo, aparece o aviso de WhatsApp desativado.
- [ ] Informar um número real (ex.: `5521988887777`), alterar o slogan, enviar uma imagem de capa e salvar.
- [ ] Toast de sucesso. No site público, o hero mostra a imagem e o botão de WhatsApp agora está ativo, com a mensagem pré-preenchida.

## 4. Categorias

- [ ] Criar a categoria "Barba" (sem informar o slug): o slug é gerado automaticamente.
- [ ] Editar a categoria e confirmar a alteração na lista.
- [ ] Criar uma categoria com o mesmo slug de outra: o erro aparece **no campo**.
- [ ] Marcar uma categoria como inativa e confirmar que ela some do site público.

## 5. Serviços (upload)

- [ ] `/painel/servicos/novo`: salvar vazio mostra os campos obrigatórios.
- [ ] Preço "55,5" é aceito e enviado como `55.50`; preço "abc" é recusado.
- [ ] Enviar um PDF ou arquivo maior que 5 MB: erro imediato no campo de imagem.
- [ ] Enviar uma imagem válida: a pré-visualização aparece.
- [ ] Criar o serviço (publicado + destaque): aparece na lista do painel e no site público.
- [ ] Editar o serviço, trocar a imagem e salvar.
- [ ] Clicar em "Ocultar": o serviço some do site público. Clicar em "Publicar": volta.
- [ ] Um serviço publicado em categoria **inativa** não aparece no site.

## 6. Barbeiros e promoções

- [ ] Criar um barbeiro com foto e confirmar em `/equipe`. Marcar como inativo e confirmar que some.
- [ ] Criar uma promoção vinculada a um serviço, com início e fim válidos: aparece na home.
- [ ] Criar uma promoção com data final anterior à inicial: o erro do backend aparece no campo.
- [ ] Uma promoção com data final no passado não aparece no site público.

## 7. Exclusões

- [ ] Excluir qualquer item abre o diálogo de confirmação. "Cancelar" não exclui e devolve o foco ao botão.
- [ ] Confirmar a exclusão de um barbeiro, uma promoção e um serviço: toast de sucesso, lista atualizada (resposta 204).
- [ ] Tentar excluir uma categoria **com serviços**: aparece o alerta de conflito (409) com a mensagem do backend.
- [ ] Excluir uma categoria sem serviços funciona.

## 8. Dashboard

- [ ] `/painel` mostra as contagens de serviços, categorias, barbeiros e promoções ativas, **iguais às listas**.
- [ ] Não existem métricas de vendas, acessos ou agendamentos.

## 9. Sessão e logout

- [ ] Em outra aba, encerrar a sessão (ou apagar o cookie `sessionid`) e tentar salvar algo: o painel avisa e volta ao login.
- [ ] Clicar em "Sair": toast, volta ao login e `/painel` volta a exigir login.
- [ ] O botão "voltar" do navegador após o logout não mostra dados do painel.

## 10. Erros de rede

- [ ] Parar o backend e abrir `/servicos`: aparece o erro com "Tentar novamente". Religar o backend e clicar: a lista carrega.
- [ ] Parar o backend, enviar o login: mensagem de falha de conexão.

## 11. Acessibilidade

- [ ] Tab no início da página mostra o "Pular para o conteúdo"; Enter leva ao conteúdo.
- [ ] Todo o fluxo funciona só com o teclado, e o foco é sempre visível.
- [ ] O menu móvel (largura < 900 px) abre com Enter e fecha com Esc, e o `aria-expanded` muda.
- [ ] Após cada navegação, o foco vai para o conteúdo principal e o título da aba muda.
- [ ] O diálogo de exclusão prende o foco e fecha com Esc.
- [ ] Erros de formulário são anunciados e o foco vai para o primeiro campo inválido.

## 12. Segurança

- [ ] Cadastrar um serviço com nome `<img src=x onerror=alert(1)>`: o texto aparece literal, sem executar.
- [ ] Nas requisições POST/PATCH/DELETE (aba Network): header `X-CSRFToken` presente e `credentials` enviados.
- [ ] Links de WhatsApp abrem em nova aba com `rel="noopener noreferrer"`.
- [ ] `/painel/login?next=//site-malicioso.com` leva a `/painel`, nunca ao site externo.