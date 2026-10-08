/**
 * Campo de upload de imagem com pré-visualização.
 * O arquivo é enviado via FormData pelo formulário (nome do campo = nome do contrato).
 */
import { html } from '../utils/dom.js';
import { resolveImageUrl } from '../utils/imageUrl.js';
import { validateImageFile } from '../utils/forms.js';

/**
 * @param {{id: string, name: string, label: string, urlAtual?: string|null, ajuda?: string}} opcoes
 * @returns {object} HTML seguro.
 */
export function ImageField({ id, name, label, urlAtual = null, ajuda = '' }) {
  const url = resolveImageUrl(urlAtual);
  return html`<div class="form-field image-field" data-image-field>
    <label for="${id}">${label}</label>
    <div class="image-field__preview" data-preview>
      ${url
        ? html`<img src="${url}" alt="Imagem atual" />`
        : html`<span class="image-field__empty">Nenhuma imagem enviada</span>`}
    </div>
    <input type="file" id="${id}" name="${name}" accept="image/jpeg,image/png,image/webp" aria-describedby="${id}-ajuda" />
    <p class="form-help" id="${id}-ajuda">${ajuda || 'JPEG, PNG ou WebP, até 5 MB.'}</p>
    <p class="image-field__status" data-preview-status role="status"></p>
  </div>`;
}

/**
 * Liga a pré-visualização e a validação local de todos os campos de imagem do container.
 * @param {ParentNode} raiz
 */
export function bindImageFields(raiz) {
  raiz.querySelectorAll('[data-image-field]').forEach((campo) => {
    const entrada = campo.querySelector('input[type="file"]');
    const previa = campo.querySelector('[data-preview]');
    const status = campo.querySelector('[data-preview-status]');
    const originalHtml = previa.innerHTML;
    let urlTemporaria = null;

    entrada.addEventListener('change', () => {
      if (urlTemporaria) {
        URL.revokeObjectURL(urlTemporaria);
        urlTemporaria = null;
      }
      entrada.removeAttribute('aria-invalid');
      campo.querySelectorAll('.field-error').forEach((el) => el.remove());

      const arquivo = entrada.files?.[0];
      if (!arquivo) {
        previa.innerHTML = originalHtml;
        status.textContent = '';
        return;
      }

      const erro = validateImageFile(arquivo);
      if (erro) {
        entrada.value = '';
        entrada.setAttribute('aria-invalid', 'true');
        status.setAttribute('role', 'alert');
        status.textContent = erro;
        previa.innerHTML = originalHtml;
        return;
      }

      urlTemporaria = URL.createObjectURL(arquivo);
      const imagem = document.createElement('img');
      imagem.src = urlTemporaria;
      imagem.alt = 'Pré-visualização da nova imagem';
      previa.replaceChildren(imagem);
      status.setAttribute('role', 'status');
      status.textContent = `Nova imagem selecionada: ${arquivo.name}`;
    });
  });
}