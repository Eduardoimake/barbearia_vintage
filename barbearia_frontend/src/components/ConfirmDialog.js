/**
 * Diálogo de confirmação reutilizável baseado em <dialog> nativo.
 * Ele já prende o foco, fecha com Esc e devolve o foco a quem o abriu.
 */
import { html, uid } from '../utils/dom.js';

/**
 * Abre o diálogo e resolve true (confirmou) ou false (cancelou).
 * @param {{titulo: string, mensagem: string, confirmar?: string, cancelar?: string, perigo?: boolean}} opcoes
 * @returns {Promise<boolean>}
 */
export function confirmDialog({
  titulo,
  mensagem,
  confirmar = 'Confirmar',
  cancelar = 'Cancelar',
  perigo = false,
}) {
  return new Promise((resolve) => {
    const anterior = document.activeElement;
    const id = uid('dialogo');
    const dialogo = document.createElement('dialog');
    dialogo.className = 'confirm-dialog';
    dialogo.setAttribute('aria-labelledby', `${id}-titulo`);
    dialogo.setAttribute('aria-describedby', `${id}-mensagem`);

    dialogo.innerHTML = String(html`<form method="dialog" class="confirm-dialog__body">
      <h2 id="${id}-titulo" class="confirm-dialog__title">${titulo}</h2>
      <p id="${id}-mensagem" class="confirm-dialog__text">${mensagem}</p>
      <div class="confirm-dialog__actions">
        <button type="submit" value="cancel" class="btn btn--ghost" autofocus>${cancelar}</button>
        <button type="submit" value="confirm" class="btn ${perigo ? 'btn--danger' : 'btn--primary'}">${confirmar}</button>
      </div>
    </form>`);

    // Clique no fundo (backdrop) cancela
    dialogo.addEventListener('click', (evento) => {
      if (evento.target === dialogo) dialogo.close('cancel');
    });

    dialogo.addEventListener('close', () => {
      const confirmado = dialogo.returnValue === 'confirm';
      dialogo.remove();
      if (anterior instanceof HTMLElement && document.contains(anterior)) anterior.focus();
      resolve(confirmado);
    });

    document.body.appendChild(dialogo);
    dialogo.showModal();
  });
}