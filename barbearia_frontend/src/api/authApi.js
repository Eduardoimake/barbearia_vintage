/**
 * Autenticação por sessão Django: /api/v1/auth/...
 */
import { request, ensureCsrf, setCsrfToken } from './client.js';

const BASE = '/api/v1/auth';

/**
 * Faz login. Obtém o CSRF antes e substitui o token pelo retornado no login.
 * A senha é enviada apenas no corpo e nunca é armazenada.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{id:number, username:string, is_staff:boolean}>}
 */
export async function login(username, password) {
  await ensureCsrf(true);
  const dados = await request(`${BASE}/login/`, {
    method: 'POST',
    json: { username, password },
  });
  if (dados?.csrfToken) setCsrfToken(dados.csrfToken);
  return dados.user;
}

/**
 * Retorna o usuário da sessão atual.
 * Lança ApiError 403 quando não há sessão.
 * @returns {Promise<object>}
 */
export async function me() {
  const dados = await request(`${BASE}/me/`);
  return dados?.user ?? dados;
}

/**
 * Encerra a sessão (204 No Content) e descarta o CSRF em memória.
 * @returns {Promise<void>}
 */
export async function logout() {
  try {
    await request(`${BASE}/logout/`, { method: 'POST' });
  } finally {
    setCsrfToken(null);
  }
}