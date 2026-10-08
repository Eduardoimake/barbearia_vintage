/**
 * Endpoints públicos: /api/v1/public/...
 */
import { request, normalizeList } from './client.js';

const BASE = '/api/v1/public';

/**
 * Dados públicos da barbearia.
 * @param {AbortSignal} [signal]
 * @returns {Promise<object>} Campos: nome_da_barbearia, slogan, numero_whatsapp, etc.
 */
export function getStore(signal) {
  return request(`${BASE}/store/`, { signal });
}

/**
 * Categorias ativas.
 * @param {AbortSignal} [signal]
 * @returns {Promise<object[]>}
 */
export async function getCategories(signal) {
  const dados = await request(`${BASE}/categories/`, { signal });
  return normalizeList(dados).results;
}

/**
 * Serviços publicados (paginado).
 * @param {{search?:string, category?:string, featured?:boolean, page?:number, page_size?:number, ordering?:string}} [filtros]
 * @param {AbortSignal} [signal]
 * @returns {Promise<{results:object[], count:number, next:string|null, previous:string|null}>}
 */
export async function getServices(filtros = {}, signal) {
  const params = {
    search: filtros.search,
    category: filtros.category,
    featured: filtros.featured ? 'true' : undefined, // a API só aceita "true"
    page: filtros.page,
    page_size: filtros.page_size,
    ordering: filtros.ordering,
  };
  return normalizeList(await request(`${BASE}/services/`, { params, signal }));
}

/**
 * Detalhe de serviço publicado.
 * @param {string} slug
 * @param {AbortSignal} [signal]
 * @returns {Promise<object>}
 */
export function getService(slug, signal) {
  return request(`${BASE}/services/${encodeURIComponent(slug)}/`, { signal });
}

/**
 * Barbeiros ativos.
 * @param {AbortSignal} [signal]
 * @returns {Promise<object[]>}
 */
export async function getBarbers(signal) {
  return normalizeList(await request(`${BASE}/barbers/`, { signal })).results;
}

/**
 * Promoções elegíveis.
 * @param {AbortSignal} [signal]
 * @returns {Promise<object[]>}
 */
export async function getPromotions(signal) {
  return normalizeList(await request(`${BASE}/promotions/`, { signal })).results;
}