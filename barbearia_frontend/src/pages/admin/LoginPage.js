/**
 * Login administrativo (/painel/login).
 * Fluxo: GET /auth/csrf/ -> POST /auth/login/ (sessão Django + CSRF).
 * A senha nunca é guardada: é lida do campo, enviada e o campo é limpo.
 */
import { html, setHtml } from '../../utils/dom.js';
import { signIn } from '../../state/authState.js';
import { showToast } from '../../components/Toast.js';
import { clearFieldErrors, showFieldErrors, applyApiError, setSubmitting } from '../../utils/forms.js';

/**
 * Aceita apenas destinos internos do painel (evita redirecionamento aberto).
 * @param {unknown} valor Parâmetro "next" da URL.
 * @returns {string}
 */
function proximoSeguro(valor) {
  if (typeof valor !== 'string') return '/painel';
  if (!valor.startsWith('/painel') || valor.startsWith('//') || valor.startsWith('/painel/login')) {
    return '/painel';
  }
  return valor;
}

/**
 * Renderiza a tela de login.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, query, navigate } = ctx;
  const destino = proximoSeguro(query.next);

  setHtml(
    root,
    html`<div class="login-card">
      <a class="brand login-card__brand" href="/" aria-label="Barbearia Vintage Co. — voltar ao site">
        <span class="brand__top">BARBEARIA</span>
        <span class="brand__bottom">Vintage Co.</span>
      </a>
      <h1 class="login-card__title">Entrar no painel</h1>
      <p class="login-card__text">Acesso restrito a administradores.</p>

      <form id="form-login" class="admin-form" novalidate>
        <div class="form-alert" data-form-alert role="alert" tabindex="-1" hidden></div>
        <div class="form-field">
          <label for="login-usuario">Usuário</label>
          <input type="text" id="login-usuario" name="username" autocomplete="username" required aria-required="true" autocapitalize="none" spellcheck="false" />
        </div>
        <div class="form-field">
          <label for="login-senha">Senha</label>
          <input type="password" id="login-senha" name="password" autocomplete="current-password" required aria-required="true" />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn--primary btn--lg" data-submit>Entrar</button>
        </div>
      </form>
      <p class="login-card__back"><a href="/">Voltar ao site</a></p>
    </div>`,
  );

  const formulario = root.querySelector('#form-login');
  const campoUsuario = root.querySelector('#login-usuario');
  const campoSenha = root.querySelector('#login-senha');

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    clearFieldErrors(formulario);

    const username = campoUsuario.value.trim();
    const password = campoSenha.value;
    const erros = {};
    if (!username) erros.username = 'Informe o usuário.';
    if (!password) erros.password = 'Informe a senha.';
    if (Object.keys(erros).length) {
      showFieldErrors(formulario, erros, 'Preencha usuário e senha.');
      return;
    }

    setSubmitting(formulario, true, 'Entrando...');
    try {
      await signIn(username, password);
      campoSenha.value = '';
      showToast('Login realizado com sucesso.', 'success');
      navigate(destino, { replace: true });
    } catch (erro) {
      campoSenha.value = '';
      setSubmitting(formulario, false);
      applyApiError(formulario, erro);
    }
  });

  campoUsuario.focus();
  return () => {
    campoSenha.value = '';
  };
}