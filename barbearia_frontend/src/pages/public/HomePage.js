/**
 * Página inicial (/). Segue a ordem de seções do homePage.html:
 * hero, categorias, serviços em destaque, promoções, sobre nós,
 * como funciona, contato e chamada final.
 * Cada seção tem seus próprios estados de carregamento, vazio e erro.
 */
import { html, setHtml } from '../../utils/dom.js';
import * as publicApi from '../../api/publicApi.js';
import { getStoreConfig, getPublicCategories } from '../../state/appState.js';
import { LoadingState } from '../../components/LoadingState.js';
import { EmptyState } from '../../components/EmptyState.js';
import { renderError } from '../../components/ErrorState.js';
import { CategoryCard } from '../../components/CategoryCard.js';
import { ServiceCard } from '../../components/ServiceCard.js';
import { PromotionCard } from '../../components/PromotionCard.js';
import { resolveImageUrl } from '../../utils/imageUrl.js';
import { whatsappButton, buildGeneralMessage } from '../../utils/whatsapp.js';

/**
 * Carrega uma seção com estados de carregamento, erro (com "Tentar novamente") e sucesso.
 * @param {HTMLElement} container Elemento da seção.
 * @param {(forcar: boolean) => Promise<any>} buscar Função que busca os dados.
 * @param {(dados: any) => void} pintar Função que desenha os dados.
 * @param {AbortSignal} signal Sinal de cancelamento da página.
 */
async function carregarSecao(container, buscar, pintar, signal) {
  const executar = async (forcar = false) => {
    setHtml(container, LoadingState('Carregando...'));
    try {
      const dados = await buscar(forcar);
      if (signal.aborted) return;
      pintar(dados);
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(container, erro, () => executar(true));
    }
  };
  await executar();
}

/**
 * Preenche o hero com os dados da barbearia (texto, botão e imagem de capa).
 * @param {HTMLElement} raiz
 * @param {object|null} loja
 */
function pintarHero(raiz, loja) {
  const texto = raiz.querySelector('[data-slot="hero-texto"]');
  const acoes = raiz.querySelector('[data-slot="hero-acoes"]');
  const visual = raiz.querySelector('[data-slot="hero-visual"]');

  if (loja?.texto_banner) texto.textContent = loja.texto_banner;

  setHtml(
    acoes,
    html`${whatsappButton({
      numero: loja?.numero_whatsapp,
      mensagem: buildGeneralMessage(loja?.nome_da_barbearia),
      rotulo: loja?.texto_botao_principal || 'Falar pelo WhatsApp',
      classe: 'btn btn--primary',
    })}
    <a class="btn btn--outline" href="/servicos">Conhecer serviços</a>`,
  );

  const urlCapa = resolveImageUrl(loja?.imagem_capa_banner);
  if (urlCapa) {
    const imagem = document.createElement('img');
    imagem.className = 'hero__image';
    imagem.src = urlCapa;
    imagem.alt = '';
    visual.prepend(imagem);
  }
}

/**
 * Renderiza a página inicial.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal } = ctx;

  setHtml(
    root,
    html`<div class="home">
      <section class="hero" aria-labelledby="hero-titulo">
        <div class="container hero__inner">
          <div class="hero__content">
            <p class="eyebrow">Barbearia contemporânea</p>
            <h1 id="hero-titulo" class="hero__title">Seu próximo visual começa aqui.</h1>
            <p class="hero__text" data-slot="hero-texto">Cortes precisos, barba impecável e uma experiência criada para quem valoriza presença, estilo e cuidado nos detalhes.</p>
            <div class="hero__actions" data-slot="hero-acoes"></div>
          </div>
          <div class="hero__visual" data-slot="hero-visual">
            <div class="hero__badge">
              <span class="hero__monogram">V Co.</span>
              <span class="hero__est">Est.</span>
            </div>
            <ul class="hero__features">
              <li>Estilo preciso</li>
              <li>Técnica clássica</li>
              <li>Acabamento contemporâneo</li>
            </ul>
          </div>
        </div>
        <a class="hero__scroll" href="#categorias">Role para explorar</a>
      </section>

      <section id="categorias" class="home-section" aria-labelledby="categorias-titulo">
        <div class="container">
          <header class="section-header">
            <p class="eyebrow">Categorias</p>
            <h2 id="categorias-titulo" class="section-title">Encontre o seu estilo</h2>
            <p class="section-text">Escolha a experiência que combina com você.</p>
            <a class="section-link" href="/servicos">Ver todos os serviços</a>
          </header>
          <div data-slot="categorias"></div>
        </div>
      </section>

      <section id="servicos" class="home-section home-section--alt" aria-labelledby="servicos-titulo">
        <div class="container">
          <header class="section-header">
            <p class="eyebrow">Serviços</p>
            <h2 id="servicos-titulo" class="section-title">Serviços selecionados</h2>
            <p class="section-text">Cuidado, técnica e personalidade em cada atendimento.</p>
          </header>
          <h3 class="subsection-title">Em destaque</h3>
          <div data-slot="servicos"></div>
          <p class="section-footer"><a class="btn btn--outline" href="/servicos">Explorar catálogo completo</a></p>
        </div>
      </section>

      <section id="promocoes" class="home-section" aria-labelledby="promocoes-titulo">
        <div class="container">
          <header class="section-header">
            <p class="eyebrow">Ofertas</p>
            <h2 id="promocoes-titulo" class="section-title">Promoções</h2>
          </header>
          <div data-slot="promocoes"></div>
        </div>
      </section>

      <section id="sobre" class="home-section home-section--alt" aria-labelledby="sobre-titulo">
        <div class="container about">
          <p class="about__number" aria-hidden="true">01</p>
          <div class="about__content">
            <p class="eyebrow">Vintage Co. · Sobre nós</p>
            <h2 id="sobre-titulo" class="section-title">Mais do que um corte. Uma experiência.</h2>
            <div data-slot="sobre"></div>
            <p><a class="btn btn--outline" href="/servicos">Conhecer nossos serviços</a></p>
          </div>
        </div>
      </section>

      <section id="como-funciona" class="home-section" aria-labelledby="como-titulo">
        <div class="container">
          <header class="section-header">
            <p class="eyebrow">Como funciona</p>
            <h2 id="como-titulo" class="section-title">Seu próximo atendimento em poucos passos</h2>
            <p class="section-text">O contato é feito diretamente pelo WhatsApp, de forma simples e pessoal.</p>
          </header>
          <ol class="steps">
            <li class="step"><span class="step__number" aria-hidden="true">1</span><h3>Escolha o serviço</h3><p>Navegue pelo catálogo e confira preço e duração de cada atendimento.</p></li>
            <li class="step"><span class="step__number" aria-hidden="true">2</span><h3>Fale pelo WhatsApp</h3><p>Envie uma mensagem direta para a equipe da barbearia.</p></li>
            <li class="step"><span class="step__number" aria-hidden="true">3</span><h3>Combine o atendimento</h3><p>Alinhe o melhor momento diretamente com a barbearia.</p></li>
          </ol>
        </div>
      </section>

      <section id="contato" class="home-section home-section--alt" aria-labelledby="contato-titulo">
        <div class="container contact-block">
          <div>
            <p class="eyebrow">Contato</p>
            <h2 id="contato-titulo" class="section-title">Visite a Barbearia Vintage Co.</h2>
            <div data-slot="contato"></div>
          </div>
          <div class="map-placeholder">
            <h3>Localização demonstrativa</h3>
            <p>O mapa será exibido quando o endereço real da barbearia for cadastrado.</p>
          </div>
        </div>
      </section>

      <section class="cta-final" aria-labelledby="cta-titulo">
        <div class="container cta-final__inner">
          <h2 id="cta-titulo" class="section-title">Seu estilo merece atenção aos detalhes.</h2>
          <p class="section-text">Escolha seu serviço e converse com a nossa equipe.</p>
          <div data-slot="cta"></div>
        </div>
      </section>
    </div>`,
  );

  const slot = (nome) => root.querySelector(`[data-slot="${nome}"]`);

  // Versão que nunca rejeita, para trechos que funcionam sem os dados da loja
  const lojaSegura = getStoreConfig().catch(() => null);

  lojaSegura.then((loja) => {
    if (signal.aborted) return;
    pintarHero(root.querySelector('.hero'), loja);
    setHtml(
      slot('cta'),
      whatsappButton({
        numero: loja?.numero_whatsapp,
        mensagem: buildGeneralMessage(loja?.nome_da_barbearia),
        rotulo: loja?.texto_botao_principal || 'Falar pelo WhatsApp',
        classe: 'btn btn--primary btn--lg',
      }),
    );
  });

  carregarSecao(
    slot('categorias'),
    (forcar) => getPublicCategories(forcar),
    (categorias) => {
      if (!categorias.length) {
        setHtml(slot('categorias'), EmptyState({ titulo: 'Nenhuma categoria disponível', mensagem: 'As categorias aparecerão aqui assim que forem cadastradas.' }));
        return;
      }
      setHtml(slot('categorias'), html`<div class="grid grid--categories">${categorias.map((c) => CategoryCard(c))}</div>`);
    },
    signal,
  );

  carregarSecao(
    slot('servicos'),
    async () => {
      const [resposta, loja] = await Promise.all([
        publicApi.getServices({ featured: true, page_size: 6 }, signal),
        lojaSegura,
      ]);
      return { resposta, loja };
    },
    ({ resposta, loja }) => {
      if (!resposta.results.length) {
        setHtml(slot('servicos'), EmptyState({ titulo: 'Nenhum serviço em destaque', mensagem: 'Veja o catálogo completo para conhecer todos os serviços.', acao: { href: '/servicos', rotulo: 'Ver catálogo' } }));
        return;
      }
      setHtml(slot('servicos'), html`<div class="grid grid--cards">${resposta.results.map((s) => ServiceCard(s, loja))}</div>`);
    },
    signal,
  );

  carregarSecao(
    slot('promocoes'),
    () => publicApi.getPromotions(signal),
    (promocoes) => {
      if (!promocoes.length) {
        setHtml(slot('promocoes'), EmptyState({ titulo: 'Sem promoções no momento', mensagem: 'Volte em breve para conferir novas ofertas.' }));
        return;
      }
      setHtml(slot('promocoes'), html`<div class="grid grid--cards">${promocoes.map((p) => PromotionCard(p))}</div>`);
    },
    signal,
  );

  carregarSecao(
    slot('sobre'),
    (forcar) => getStoreConfig(forcar),
    (loja) => {
      setHtml(slot('sobre'), html`<p class="section-text section-text--lg">${loja.descricao_apresentacao}</p>`);
    },
    signal,
  );

  carregarSecao(
    slot('contato'),
    (forcar) => getStoreConfig(forcar),
    (loja) => {
      setHtml(
        slot('contato'),
        html`<dl class="info-list">
          <div><dt>Endereço</dt><dd>${loja.endereco_demo}</dd></div>
          <div><dt>Horário de atendimento</dt><dd>${loja.horario_atendimento}</dd></div>
        </dl>
        <p><a class="btn btn--outline" href="/contato">Ver página de contato</a></p>`,
      );
    },
    signal,
  );

  return () => {};
}