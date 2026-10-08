/**
 * Formatadores e normalizadores de valores (preço, duração, datas).
 * Os decimais são tratados como string para nunca perder casas (ex.: "55.00").
 */

/**
 * Normaliza um valor decimal para o formato da API: "55.00".
 * Aceita "55.00", "55,5", "1.234,56", "R$ 55" ou número.
 * @param {string|number|null|undefined} valor
 * @returns {string|null} String com 2 casas decimais, ou null se inválido.
 */
export function normalizeDecimal(valor) {
  if (valor === null || valor === undefined) return null;
  let texto = String(valor).trim().replace(/R\$/gi, '').replace(/\s+/g, '');
  if (texto === '') return null;

  const temVirgula = texto.includes(',');
  const temPonto = texto.includes('.');

  if (temVirgula && temPonto) {
    // O último separador é o decimal; o outro é separador de milhar
    if (texto.lastIndexOf(',') > texto.lastIndexOf('.')) {
      texto = texto.replace(/\./g, '').replace(',', '.');
    } else {
      texto = texto.replace(/,/g, '');
    }
  } else if (temVirgula) {
    texto = texto.replace(/\./g, '').replace(',', '.');
  } else if (temPonto && (texto.match(/\./g) || []).length > 1) {
    // Vários pontos: são milhares (1.234.567)
    texto = texto.replace(/\./g, '');
  }

  if (!/^\d+(\.\d{1,2})?$/.test(texto)) return null;

  const [inteiro, decimal = ''] = texto.split('.');
  return `${inteiro.replace(/^0+(?=\d)/, '')}.${decimal.padEnd(2, '0')}`;
}

/**
 * Formata preço decimal em string para moeda brasileira, sem usar ponto flutuante.
 * @param {string|number|null|undefined} valor Ex.: "55.00".
 * @returns {string} Ex.: "R$ 55,00".
 */
export function formatPrice(valor) {
  const normalizado = normalizeDecimal(valor);
  if (normalizado === null) return 'Preço sob consulta';
  const [inteiro, decimal] = normalizado.split('.');
  const comMilhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${comMilhar},${decimal}`;
}

/**
 * Formata duração em minutos.
 * @param {number|string|null|undefined} minutos
 * @returns {string} Ex.: "45 min" ou "1h 30min".
 */
export function formatDuration(minutos) {
  const total = Number.parseInt(String(minutos), 10);
  if (!Number.isFinite(total) || total <= 0) return 'Duração a combinar';
  if (total < 60) return `${total} min`;
  const horas = Math.floor(total / 60);
  const resto = total % 60;
  return resto ? `${horas}h ${resto}min` : `${horas}h`;
}

/**
 * Formata data/hora ISO em pt-BR.
 * @param {string|null|undefined} iso
 * @returns {string}
 */
export function formatDate(iso) {
  if (!iso) return '—';
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return '—';
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(data);
}

/**
 * Converte ISO da API para o valor de <input type="datetime-local">.
 * @param {string|null|undefined} iso
 * @returns {string}
 */
export function toDatetimeLocal(iso) {
  if (!iso) return '';
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return '';
  const p = (n) => String(n).padStart(2, '0');
  return `${data.getFullYear()}-${p(data.getMonth() + 1)}-${p(data.getDate())}T${p(data.getHours())}:${p(data.getMinutes())}`;
}

/**
 * Converte o valor de <input type="datetime-local"> para ISO (UTC) da API.
 * @param {string|null|undefined} valor
 * @returns {string|null}
 */
export function fromDatetimeLocal(valor) {
  if (!valor) return null;
  const data = new Date(valor);
  return Number.isNaN(data.getTime()) ? null : data.toISOString();
}

/**
 * Converte texto em inteiro não negativo, ou null se vazio/inválido.
 * @param {string|number|null|undefined} valor
 * @returns {number|null}
 */
export function toInt(valor) {
  if (valor === null || valor === undefined || String(valor).trim() === '') return null;
  const n = Number.parseInt(String(valor), 10);
  return Number.isFinite(n) ? n : null;
}