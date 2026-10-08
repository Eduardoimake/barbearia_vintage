/**
 * Cache em memória dos dados públicos usados em várias telas
 * (loja e categorias). Erros nunca são guardados em cache.
 */
import * as publicApi from '../api/publicApi.js';

const cache = { loja: null, categorias: null };
const pendentes = { loja: null, categorias: null };

/**
 * Carrega com cache e deduplicação de chamadas simultâneas.
 * @param {'loja'|'categorias'} chave
 * @param {() => Promise<any>} carregar
 * @param {boolean} forcar
 */
async function obter(chave, carregar, forcar) {
  if (!forcar && cache[chave]) return cache[chave];
  if (!forcar && pendentes[chave]) return pendentes[chave];
  pendentes[chave] = carregar()
    .then((dados) => {
      cache[chave] = dados;
      return dados;
    })
    .finally(() => {
      pendentes[chave] = null;
    });
  return pendentes[chave];
}

/**
 * Dados públicos da barbearia (com cache).
 * @param {boolean} [forcar]
 * @returns {Promise<object>}
 */
export function getStoreConfig(forcar = false) {
  return obter('loja', () => publicApi.getStore(), forcar);
}

/**
 * Categorias públicas (com cache).
 * @param {boolean} [forcar]
 * @returns {Promise<object[]>}
 */
export function getPublicCategories(forcar = false) {
  return obter('categorias', () => publicApi.getCategories(), forcar);
}

/** Invalida o cache após alterações no painel. */
export function clearPublicCache() {
  cache.loja = null;
  cache.categorias = null;
}