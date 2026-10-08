/**
 * Estado de autenticação apenas em memória.
 * O frontend melhora a experiência; o backend é a autoridade.
 */
import * as authApi from '../api/authApi.js';

const estado = { usuario: null, verificado: false };
const ouvintes = new Set();

/** Notifica os assinantes sobre mudanças. */
function notificar() {
  ouvintes.forEach((fn) => fn({ ...estado }));
}

/**
 * Assina mudanças do estado de autenticação.
 * @param {(estado: {usuario: object|null, verificado: boolean}) => void} fn
 * @returns {() => void} Função para cancelar a assinatura.
 */
export function subscribeAuth(fn) {
  ouvintes.add(fn);
  return () => ouvintes.delete(fn);
}

/** @returns {object|null} Usuário autenticado ou null. */
export function getUser() {
  return estado.usuario;
}

/** @returns {boolean} Se há administrador autenticado. */
export function isAuthenticated() {
  return Boolean(estado.usuario?.is_staff);
}

/** @returns {boolean} Se a sessão já foi verificada no backend. */
export function isChecked() {
  return estado.verificado;
}

/**
 * Verifica a sessão existente no backend (GET /auth/me/).
 * @returns {Promise<object|null>}
 */
export async function restoreSession() {
  try {
    const usuario = await authApi.me();
    estado.usuario = usuario?.is_staff ? usuario : null;
  } catch {
    estado.usuario = null;
  }
  estado.verificado = true;
  notificar();
  return estado.usuario;
}

/**
 * Realiza login e guarda o usuário em memória.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<object>}
 */
export async function signIn(username, password) {
  const usuario = await authApi.login(username, password);
  estado.usuario = usuario;
  estado.verificado = true;
  notificar();
  return usuario;
}

/**
 * Encerra a sessão e limpa o estado local, mesmo se o backend falhar.
 * @returns {Promise<void>}
 */
export async function signOut() {
  try {
    await authApi.logout();
  } finally {
    clearSession();
  }
}

/** Limpa o estado local (ex.: após 401/403 em rota administrativa). */
export function clearSession() {
  estado.usuario = null;
  estado.verificado = true;
  notificar();
}