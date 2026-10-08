/**
 * Notificações temporárias (toasts) acessíveis.
 * Erros usam role="alert"; demais usam role="status".
 */

/**
 * Exibe uma notificação.
 * @param {string} mensagem
 * @param {'success'|'error'|'info'} [tipo]
 * @param {number} [duracaoMs]
 */
export function showToast(mensagem, tipo = 'success', duracaoMs = 5000) {
  const regiao = document.getElementById('toast-region');
  if (!regiao) return;

  const toast = document.createElement('div');
  toast.className = `toast toast--${tipo}`;
  toast.setAttribute('role', tipo === 'error' ? 'alert' : 'status');

  const texto = document.createElement('span');
  texto.className = 'toast__text';
  texto.textContent = mensagem; // textContent evita injeção de HTML

  const fechar = document.createElement('button');
  fechar.type = 'button';
  fechar.className = 'toast__close';
  fechar.setAttribute('aria-label', 'Fechar notificação');
  fechar.textContent = '×';

  const remover = () => toast.remove();
  fechar.addEventListener('click', remover);

  toast.append(texto, fechar);
  regiao.appendChild(toast);
  window.setTimeout(remover, duracaoMs);
}