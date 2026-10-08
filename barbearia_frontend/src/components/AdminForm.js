/**
 * Formulário administrativo reutilizável, gerado a partir de definições de campos.
 *
 * Definição de campo:
 * {
 *   name, label, type: 'text'|'textarea'|'number'|'decimal'|'select'|'checkbox'|'datetime'|'image',
 *   required?, ajuda?, rows?, maxlength?, min?, placeholder?,
 *   opcoes?: [{valor, rotulo}]   // select
 *   omitirSeVazio?: boolean      // não envia o campo quando vazio (ex.: slug na criação)
 * }
 */
import { html, raw } from '../utils/dom.js';
import { ImageField } from './ImageField.js';
import { normalizeDecimal, fromDatetimeLocal, toInt } from '../utils/formatters.js';
import { validateImageFile } from '../utils/forms.js';

/**
 * Atributos comuns de um campo (obrigatório, ajuda).
 * @param {object} campo
 * @param {string} idCampo
 * @returns {object} HTML seguro com atributos.
 */
function atributosComuns(campo, idCampo) {
  const partes = [];
  if (campo.required) partes.push('required aria-required="true"');
  if (campo.ajuda) partes.push(`aria-describedby="${idCampo}-ajuda"`);
  return raw(partes.join(' '));
}

/**
 * Renderiza um único campo.
 * @param {string} idForm
 * @param {object} campo
 * @param {Record<string, any>} valores
 * @returns {object} HTML seguro.
 */
function renderCampo(idForm, campo, valores) {
  const idCampo = `${idForm}-${campo.name}`;
  const tipo = campo.type || 'text';
  const valor = valores[campo.name] ?? campo.padrao ?? '';
  const ajuda = campo.ajuda ? html`<p class="form-help" id="${idCampo}-ajuda">${campo.ajuda}</p>` : '';
  const rotulo = html`<label for="${idCampo}">${campo.label}${campo.required ? html` <span class="required" aria-hidden="true">*</span>` : ''}</label>`;

  if (tipo === 'image') {
    return ImageField({ id: idCampo, name: campo.name, label: campo.label, urlAtual: valor || null, ajuda: campo.ajuda });
  }

  if (tipo === 'checkbox') {
    const marcado = valor === true || valor === 'true';
    return html`<div class="form-field form-field--check">
      <label class="check" for="${idCampo}">
        <input type="checkbox" id="${idCampo}" name="${campo.name}" value="true" ${marcado ? raw('checked') : ''} ${atributosComuns({ ...campo, required: false }, idCampo)} />
        <span>${campo.label}</span>
      </label>
      ${ajuda}
    </div>`;
  }

  if (tipo === 'textarea') {
    return html`<div class="form-field">
      ${rotulo}
      <textarea id="${idCampo}" name="${campo.name}" rows="${campo.rows || 4}" ${campo.maxlength ? raw(`maxlength="${Number(campo.maxlength)}"`) : ''} ${atributosComuns(campo, idCampo)}>${valor}</textarea>
      ${ajuda}
    </div>`;
  }

  if (tipo === 'select') {
    return html`<div class="form-field">
      ${rotulo}
      <select id="${idCampo}" name="${campo.name}" ${atributosComuns(campo, idCampo)}>
        <option value="">${campo.placeholder || 'Selecione...'}</option>
        ${(campo.opcoes || []).map(
          (o) => html`<option value="${o.valor}" ${String(o.valor) === String(valor) ? raw('selected') : ''}>${o.rotulo}</option>`,
        )}
      </select>
      ${ajuda}
    </div>`;
  }

  // Campos de entrada simples
  let tipoHtml = 'text';
  let extras = '';
  if (tipo === 'number') {
    tipoHtml = 'number';
    extras = `inputmode="numeric" step="1" ${campo.min !== undefined ? `min="${Number(campo.min)}"` : ''}`;
  } else if (tipo === 'decimal') {
    extras = 'inputmode="decimal"';
  } else if (tipo === 'datetime') {
    tipoHtml = 'datetime-local';
  }

  return html`<div class="form-field">
    ${rotulo}
    <input type="${tipoHtml}" id="${idCampo}" name="${campo.name}" value="${valor}" ${campo.maxlength ? raw(`maxlength="${Number(campo.maxlength)}"`) : ''} ${campo.placeholder ? raw(`placeholder="${String(campo.placeholder).replace(/"/g, '&quot;')}"`) : ''} ${raw(extras)} ${atributosComuns(campo, idCampo)} />
    ${ajuda}
  </div>`;
}

/**
 * Gera o formulário completo.
 * @param {{id: string, campos: object[], valores?: Record<string, any>, enviar?: string, cancelarHref?: string|null}} opcoes
 * @returns {object} HTML seguro.
 */
export function AdminForm({ id, campos, valores = {}, enviar = 'Salvar', cancelarHref = null }) {
  return html`<form id="${id}" class="admin-form" novalidate>
    <div class="form-alert" data-form-alert role="alert" tabindex="-1" hidden></div>
    ${campos.map((c) => renderCampo(id, c, valores))}
    <div class="form-actions">
      <button type="submit" class="btn btn--primary" data-submit>${enviar}</button>
      ${cancelarHref ? html`<a class="btn btn--ghost" href="${cancelarHref}">Cancelar</a>` : ''}
    </div>
  </form>`;
}

/**
 * Lê e valida (no cliente) os valores do formulário, convertendo os tipos.
 * O backend continua sendo a autoridade da validação.
 * - decimal: string normalizada ("55.00")
 * - number: inteiro ou null
 * - datetime: ISO ou null
 * - select/campos vazios opcionais: null (ou '' para texto)
 * - image: File somente quando um arquivo novo foi escolhido
 * @param {HTMLFormElement} formulario
 * @param {object[]} campos
 * @returns {{valores: Record<string, any>, erros: Record<string, string>}}
 */
export function readForm(formulario, campos) {
  const valores = {};
  const erros = {};

  for (const campo of campos) {
    const elemento = formulario.elements[campo.name];
    if (!elemento) continue;
    const tipo = campo.type || 'text';

    if (tipo === 'checkbox') {
      valores[campo.name] = Boolean(elemento.checked);
      continue;
    }

    if (tipo === 'image') {
      const arquivo = elemento.files?.[0];
      const erroImagem = validateImageFile(arquivo);
      if (erroImagem) erros[campo.name] = erroImagem;
      else if (arquivo) valores[campo.name] = arquivo;
      continue;
    }

    const bruto = String(elemento.value ?? '').trim();
    const vazio = bruto === '';

    if (vazio) {
      if (campo.required) {
        erros[campo.name] = 'Este campo é obrigatório.';
      } else if (!campo.omitirSeVazio) {
        valores[campo.name] = ['text', 'textarea'].includes(tipo) ? '' : null;
      }
      continue;
    }

    if (tipo === 'decimal') {
      const decimal = normalizeDecimal(bruto);
      if (decimal === null) erros[campo.name] = 'Informe um valor válido, por exemplo 55.00.';
      else valores[campo.name] = decimal;
    } else if (tipo === 'number') {
      const inteiro = toInt(bruto);
      if (inteiro === null) erros[campo.name] = 'Informe um número inteiro.';
      else if (campo.min !== undefined && inteiro < campo.min) erros[campo.name] = `O valor mínimo é ${campo.min}.`;
      else valores[campo.name] = inteiro;
    } else if (tipo === 'datetime') {
      const iso = fromDatetimeLocal(bruto);
      if (iso === null) erros[campo.name] = 'Informe uma data e hora válidas.';
      else valores[campo.name] = iso;
    } else if (tipo === 'select') {
      valores[campo.name] = bruto;
    } else {
      valores[campo.name] = bruto;
    }
  }

  return { valores, erros };
}