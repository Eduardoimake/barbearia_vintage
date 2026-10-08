/**
 * Cliente HTTP central. Único ponto que usa fetch.
 * - credentials: "include" (sessão Django)
 * - CSRF em memória, enviado em X-CSRFToken (POST/PATCH/DELETE)
 * - 204 No Content retorna null (sem response.json())
 * - Erros padronizados em ApiError
 */
import { ApiError } from '../utils/errors.js';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const TEMPO_LIMITE_MS = 20000;
const METODOS_ESCRITA = ['POST', 'PUT', 'PATCH', 'DELETE'];

/** Token CSRF mantido apenas em memória (nunca em localStorage). */
let tokenCsrf = null;

/** Callback chamado quando uma rota admin retorna 401/403. */
let aoFalharAutenticacao = null;

/**
 * Registra o tratador de falha de autenticação em rotas administrativas.
 * @param {(() => void)|null} funcao
 */
export function setAuthFailureHandler(funcao) {
  aoFalharAutenticacao = funcao;
}

/**
 * Define o token CSRF em memória.
 * @param {string|null} token
 */
export function setCsrfToken(token) {
  tokenCsrf = token || null;
}

/**
 * Retorna o token CSRF atual (ou null).
 * @returns {string|null}
 */
export function getCsrfToken() {
  return tokenCsrf;
}

/**
 * Monta a URL final com query string, ignorando valores vazios.
 * @param {string} caminho
 * @param {Record<string, any>} [params]
 * @returns {string}
 */
function montarUrl(caminho, params) {
  const url = `${API_BASE}${caminho}`;
  if (!params) return url;
  const busca = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== null && String(valor) !== '') {
      busca.append(chave, String(valor));
    }
  }
  const texto = busca.toString();
  return texto ? `${url}?${texto}` : url;
}

/**
 * Lê o corpo da resposta de forma segura (JSON, texto ou vazio).
 * @param {Response} resposta
 * @returns {Promise<any>}
 */
async function lerCorpo(resposta) {
  if (resposta.status === 204 || resposta.status === 205) return null;
  const tipo = resposta.headers.get('content-type') || '';
  if (tipo.includes('application/json')) {
    try {
      return await resposta.json();
    } catch {
      return null;
    }
  }
  try {
    const texto = await resposta.text();
    return texto ? { _texto: texto.slice(0, 300) } : null;
  } catch {
    return null;
  }
}

/**
 * Obtém e guarda o token CSRF em memória (GET /api/v1/auth/csrf/).
 * @param {boolean} [forcar] Ignora o token já guardado.
 * @returns {Promise<string>}
 */
export async function ensureCsrf(forcar = false) {
  if (tokenCsrf && !forcar) return tokenCsrf;
  const dados = await request('/api/v1/auth/csrf/', { semCsrf: true });
  tokenCsrf = dados?.csrfToken || null;
  if (!tokenCsrf) throw new ApiError(500, 'O servidor não retornou o token CSRF.');
  return tokenCsrf;
}

/**
 * Executa uma requisição à API.
 * @param {string} caminho Ex.: "/api/v1/public/store/".
 * @param {object} [opcoes]
 * @param {string} [opcoes.method]
 * @param {Record<string, any>} [opcoes.params] Query string.
 * @param {object} [opcoes.json] Corpo JSON.
 * @param {FormData} [opcoes.formData] Corpo multipart (sem Content-Type manual).
 * @param {AbortSignal} [opcoes.signal]
 * @param {boolean} [opcoes.semCsrf] Não anexar CSRF.
 * @param {boolean} [opcoes._tentouRenovar] Uso interno (retry de CSRF).
 * @returns {Promise<any>} JSON ou null (204).
 */
export async function request(caminho, opcoes = {}) {
  const { method = 'GET', params, json, formData, signal, semCsrf = false } = opcoes;
  const metodo = method.toUpperCase();
  const escrita = METODOS_ESCRITA.includes(metodo);

  const cabecalhos = { Accept: 'application/json' };
  if (escrita && !semCsrf) {
    cabecalhos['X-CSRFToken'] = await ensureCsrf();
  }

  let corpo;
  if (formData) {
    corpo = formData; // o navegador define o boundary do multipart
  } else if (json !== undefined) {
    cabecalhos['Content-Type'] = 'application/json';
    corpo = JSON.stringify(json);
  }

  const controlador = new AbortController();
  const temporizador = window.setTimeout(() => controlador.abort(), TEMPO_LIMITE_MS);
  if (signal) signal.addEventListener('abort', () => controlador.abort(), { once: true });

  let resposta;
  try {
    resposta = await fetch(montarUrl(caminho, params), {
      method: metodo,
      headers: cabecalhos,
      body: corpo,
      credentials: 'include',
      signal: controlador.signal,
    });
  } catch (erro) {
    if (signal?.aborted) throw erro; // cancelamento intencional
    throw new ApiError(0, 'Falha de rede ou tempo esgotado.');
  } finally {
    window.clearTimeout(temporizador);
  }

  const dados = await lerCorpo(resposta);

  if (resposta.ok) return dados; // inclui 204 -> null

const textoDetalhe = typeof dados?.detail === 'string' ? dados.detail : '';
const textoBruto = `${textoDetalhe} ${dados?._texto || ''}`;

  // Token CSRF expirado/rotacionado: renova e tenta uma única vez
  if (
    resposta.status === 403 &&
    escrita &&
    !semCsrf &&
    !opcoes._tentouRenovar &&
    /csrf/i.test(textoBruto)
  ) {
    await ensureCsrf(true);
    return request(caminho, { ...opcoes, _tentouRenovar: true });
  }

  const retry = Number.parseInt(resposta.headers.get('Retry-After') || '', 10);
  const erro = new ApiError(
    resposta.status,
    textoDetalhe || `Erro ${resposta.status}`,
    dados,
    Number.isFinite(retry) ? retry : null,
  );

  // Falha de autenticação em rota administrativa: notifica a aplicação
  if (
    (resposta.status === 401 || resposta.status === 403) &&
    caminho.includes('/api/v1/admin/') &&
    aoFalharAutenticacao
  ) {
    aoFalharAutenticacao();
  }
  throw erro;
}

/**
 * Normaliza respostas de lista: aceita array puro ou objeto paginado.
 * @param {any} dados
 * @returns {{results: any[], count: number, next: string|null, previous: string|null}}
 */
export function normalizeList(dados) {
  if (Array.isArray(dados)) {
    return { results: dados, count: dados.length, next: null, previous: null };
  }
  const results = Array.isArray(dados?.results) ? dados.results : [];
  return {
    results,
    count: Number.isFinite(dados?.count) ? dados.count : results.length,
    next: dados?.next ?? null,
    previous: dados?.previous ?? null,
  };
}