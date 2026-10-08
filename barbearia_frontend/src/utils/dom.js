/**
 * Utilitários de DOM e renderização segura.
 * O template `html` escapa todo valor interpolado, exceto os marcados com `raw()`.
 */

const MAPA_ESCAPE = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '`': '&#96;',
};

/**
 * Escapa texto para uso seguro em HTML (conteúdo e atributos).
 * @param {unknown} valor
 * @returns {string}
 */
export function escapeHtml(valor) {
  if (valor === null || valor === undefined) return '';
  return String(valor).replace(/[&<>"'`]/g, (c) => MAPA_ESCAPE[c]);
}

/** Representa um trecho de HTML já confiável (não será escapado novamente). */
class HtmlSeguro {
  /** @param {string} texto */
  constructor(texto) {
    this.texto = texto;
  }

  toString() {
    return this.texto;
  }
}

/**
 * Marca um texto como HTML confiável. Use apenas com HTML produzido por `html`.
 * @param {string} texto
 * @returns {HtmlSeguro}
 */
export function raw(texto) {
  return new HtmlSeguro(String(texto ?? ''));
}

/**
 * Converte um valor interpolado em string segura.
 * @param {unknown} valor
 * @returns {string}
 */
function converter(valor) {
  if (valor instanceof HtmlSeguro) return valor.texto;
  if (Array.isArray(valor)) return valor.map(converter).join('');
  if (valor === null || valor === undefined || valor === false) return '';
  return escapeHtml(valor);
}

/**
 * Template literal que escapa automaticamente os valores interpolados.
 * @param {TemplateStringsArray} partes
 * @param {...unknown} valores
 * @returns {HtmlSeguro}
 */
export function html(partes, ...valores) {
  let saida = '';
  partes.forEach((parte, i) => {
    saida += parte;
    if (i < valores.length) saida += converter(valores[i]);
  });
  return new HtmlSeguro(saida);
}

/**
 * Atribui HTML seguro a um elemento.
 * @param {Element} elemento
 * @param {HtmlSeguro|string} conteudo Deve vir de `html`/`raw`.
 */
export function setHtml(elemento, conteudo) {
  elemento.innerHTML = conteudo instanceof HtmlSeguro ? conteudo.texto : escapeHtml(conteudo);
}

/**
 * Atalho para querySelector.
 * @param {string} seletor
 * @param {ParentNode} [raiz]
 * @returns {Element|null}
 */
export function $(seletor, raiz = document) {
  return raiz.querySelector(seletor);
}

/**
 * Atalho para querySelectorAll, retornando array.
 * @param {string} seletor
 * @param {ParentNode} [raiz]
 * @returns {Element[]}
 */
export function $$(seletor, raiz = document) {
  return Array.from(raiz.querySelectorAll(seletor));
}

/**
 * Anuncia uma mensagem para leitores de tela via aria-live.
 * @param {string} mensagem
 */
export function announce(mensagem) {
  const regiao = document.getElementById('live-region');
  if (!regiao) return;
  regiao.textContent = '';
  // Pequeno atraso garante que a mudança seja percebida pelos leitores de tela
  window.setTimeout(() => {
    regiao.textContent = mensagem;
  }, 50);
}

/**
 * Move o foco para #main-content (acessibilidade após navegação).
 */
export function focusMain() {
  const main = document.getElementById('main-content');
  if (!main) return;
  if (!main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1');
  main.focus({ preventScroll: false });
}

/**
 * Cria uma versão com atraso de uma função (útil para busca).
 * @param {Function} funcao
 * @param {number} [atrasoMs]
 * @returns {Function}
 */
export function debounce(funcao, atrasoMs = 350) {
  let temporizador;
  return (...args) => {
    window.clearTimeout(temporizador);
    temporizador = window.setTimeout(() => funcao(...args), atrasoMs);
  };
}

/**
 * Gera um id único curto para associar labels e mensagens.
 * @param {string} [prefixo]
 * @returns {string}
 */
export function uid(prefixo = 'id') {
  return `${prefixo}-${Math.random().toString(36).slice(2, 9)}`;
}