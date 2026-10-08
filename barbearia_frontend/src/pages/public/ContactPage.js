/**
 * Contato (/contato): endereço, horário e WhatsApp, vindos de /public/store/.
 * O número fictício do seed não gera link ativo.
 */
import { html, setHtml } from '../../utils/dom.js';
import { getStoreConfig } from '../../state/appState.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';
import {
  whatsappButton,
  buildGeneralMessage,
  isDemoNumber,
  isValidWhatsAppNumber,
  normalizeWhatsAppNumber,
} from '../../utils/whatsapp.js';

/**
 * Renderiza a página de contato.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal } = ctx;

  setHtml(
    root,
    html`<div class="container page">
      <header class="page-header">
        <h1 class="page-title">Contato</h1>
        <p class="page-subtitle">Fale diretamente com a nossa equipe.</p>
      </header>
      <div data-conteudo></div>
    </div>`,
  );
  const conteudo = root.querySelector('[data-conteudo]');

  const carregar = async (forcar = false) => {
    setHtml(conteudo, LoadingState('Carregando informações...'));
    try {
      const loja = await getStoreConfig(forcar);
      if (signal.aborted) return;

      const numeroValido = isValidWhatsAppNumber(loja.numero_whatsapp);
      const demonstrativo = isDemoNumber(loja.numero_whatsapp);
      const digitos = normalizeWhatsAppNumber(loja.numero_whatsapp);

      let textoWhatsapp = 'WhatsApp não configurado.';
      if (numeroValido && demonstrativo) {
        textoWhatsapp = 'O número cadastrado é demonstrativo. O contato por WhatsApp ficará disponível quando o número real for informado.';
      } else if (numeroValido) {
        textoWhatsapp = `+${digitos}`;
      }

      setHtml(
        conteudo,
        html`<div class="contact-grid">
          <section class="contact-card" aria-labelledby="contato-info">
            <h2 id="contato-info" class="contact-card__title">${loja.nome_da_barbearia}</h2>
            ${loja.slogan ? html`<p class="contact-card__text">${loja.slogan}</p>` : ''}
            <dl class="info-list">
              <div><dt>Endereço</dt><dd>${loja.endereco_demo}</dd></div>
              <div><dt>Horário de atendimento</dt><dd>${loja.horario_atendimento}</dd></div>
              <div><dt>WhatsApp</dt><dd>${textoWhatsapp}</dd></div>
            </dl>
            <p>
              ${whatsappButton({
                numero: loja.numero_whatsapp,
                mensagem: buildGeneralMessage(loja.nome_da_barbearia),
                rotulo: loja.texto_botao_principal || 'Falar pelo WhatsApp',
                classe: 'btn btn--primary',
              })}
            </p>
          </section>
          <div class="map-placeholder">
            <h2>Localização demonstrativa</h2>
            <p>O mapa será exibido quando o endereço real da barbearia for cadastrado.</p>
          </div>
        </div>`,
      );
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(conteudo, erro, () => carregar(true), 'Não foi possível carregar o contato');
    }
  };

  await carregar();
  return () => {};
}