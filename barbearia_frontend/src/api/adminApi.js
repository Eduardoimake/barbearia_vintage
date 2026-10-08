/**
 * Endpoints administrativos: /api/v1/admin/...
 * `corpo` deve vir de buildRequestBody(): {json} ou {formData}.
 */
import { request, normalizeList } from './client.js';

const BASE = '/api/v1/admin';
const TAMANHO_PAGINA_MAX = 50;

/**
 * Cria o conjunto de operações CRUD de um recurso.
 * @param {string} recurso Ex.: "services".
 */
function criarRecurso(recurso) {
  const raiz = `${BASE}/${recurso}/`;
  return {
    /**
     * Lista paginada.
     * @param {{page?:number, page_size?:number}} [params]
     */
    async list(params = {}, signal) {
      return normalizeList(await request(raiz, { params, signal }));
    },

    /** Busca todas as páginas (útil para selects). */
    async listAll(signal) {
      const primeira = await this.list({ page: 1, page_size: TAMANHO_PAGINA_MAX }, signal);
      const todos = [...primeira.results];
      const paginas = Math.ceil(primeira.count / TAMANHO_PAGINA_MAX);
      for (let pagina = 2; pagina <= paginas; pagina += 1) {
        const resp = await this.list({ page: pagina, page_size: TAMANHO_PAGINA_MAX }, signal);
        todos.push(...resp.results);
      }
      return todos;
    },

    /** Detalhe por id. */
    get(id, signal) {
      return request(`${raiz}${encodeURIComponent(id)}/`, { signal });
    },

    /** Criação (POST). */
    create(corpo) {
      return request(raiz, { method: 'POST', ...corpo });
    },

    /** Edição parcial (PATCH). */
    update(id, corpo) {
      return request(`${raiz}${encodeURIComponent(id)}/`, { method: 'PATCH', ...corpo });
    },

    /** Exclusão (DELETE, 204 -> null). */
    remove(id) {
      return request(`${raiz}${encodeURIComponent(id)}/`, { method: 'DELETE' });
    },
  };
}

export const servicesApi = criarRecurso('services');
export const categoriesApi = criarRecurso('categories');
export const barbersApi = criarRecurso('barbers');
export const promotionsApi = criarRecurso('promotions');

/**
 * Contagens reais do dashboard.
 * @returns {Promise<{services_count:number, categories_count:number, barbers_count:number, active_promotions_count:number}>}
 */
export function getDashboard(signal) {
  return request(`${BASE}/dashboard/`, { signal });
}

/**
 * Configuração da barbearia (GET).
 * @returns {Promise<object>}
 */
export function getAdminStore(signal) {
  return request(`${BASE}/store/`, { signal });
}

/**
 * Atualiza a configuração da barbearia (PATCH).
 * @param {{json?:object, formData?:FormData}} corpo
 * @returns {Promise<object>}
 */
export function updateAdminStore(corpo) {
  return request(`${BASE}/store/`, { method: 'PATCH', ...corpo });
}