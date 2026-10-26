
import ValidarIngressos from './ValidarIngressos.jsx';
import { useEffect, useState } from 'react';
import {
  CalendarDays,
  Clock3,
  MapPin,
  Ticket,
  Music2,
  Utensils,
  Martini,
  Minus,
  Plus,
  ShieldCheck,
  Sparkles,
  CheckCircle,
  Download,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';


const API_URL = (
  import.meta.env.VITE_API_URL ||
  'https://cristoteca-todos-santos.onrender.com'
).replace(/\/$/, '');

const PRICE_CENTS = 500;


export default function App() {
  const [quantity, setQuantity] = useState(1);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);

  const [returnedOrderId, setReturnedOrderId] = useState('');
  const [paymentResult, setPaymentResult] = useState(null);
  const [paymentError, setPaymentError] = useState('');
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [paymentCheckKey, setPaymentCheckKey] = useState(0);
  const [restoringOrder, setRestoringOrder] = useState(true);

  const money = (cents) =>
    (cents / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });



async function verifyPayment(pedidoId) {
  if (!pedidoId) return;

  setCheckingPayment(true);
  setPaymentError('');
  setPaymentResult(null);

  try {
    for (let tentativa = 1; tentativa <= 10; tentativa++) {
      const response = await fetch(
        `${API_URL}/api/pagamentos/pedido/${pedidoId}/status`,
        { cache: 'no-store' }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || 'Não foi possível consultar o pagamento.'
        );
      }

      if (
        data.status_pagamento === 'aprovado' &&
        data.status_pedido === 'pago'
      ) {
        setReturnedOrderId(pedidoId);
        setPaymentResult({
          ...data,
          pedido_id: data.pedido_id || pedidoId,
        });
        setPaymentError('');
        return;
      }

      if (tentativa < 10) {
        await new Promise((resolve) => setTimeout(resolve, 3000));
      } else {
        setPaymentError(
          'Ainda estamos aguardando a confirmação. Clique abaixo para consultar novamente.'
        );
      }
    }
  } catch (error) {
    console.error('Erro ao verificar pagamento:', error);
    setPaymentError(
      error.message || 'Não foi possível verificar o pagamento.'
    );
  } finally {
    setCheckingPayment(false);
  }
}



  useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const pedidoId = params.get('pedido_id');
  const retorno = params.get('retorno');

  if (!pedidoId) {
    setRestoringOrder(false);
    return;
  }

  setReturnedOrderId(pedidoId);

  if (retorno === 'falha') {
    setPaymentError(
      'O pagamento não foi concluído. Você pode verificar novamente.'
    );
    setRestoringOrder(false);
    return;
  }

  verifyPayment(pedidoId).finally(() => {
    setRestoringOrder(false);
  });
}, []);

  async function startPurchase(event) {
    event.preventDefault();

    if (loading) return;

    if (name.trim().length < 2) {
      alert('Informe seu nome completo.');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      alert('Informe um e-mail válido.');
      return;
    }

    setLoading(true);

    try {
      const pedidoResponse = await fetch(
        `${API_URL}/api/pedidos`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            nome_comprador: name.trim(),
            email: email.trim().toLowerCase(),
            telefone: phone.trim() || null,
            quantidade: quantity,
          }),
        }
      );

      const pedidoData = await pedidoResponse.json();

      if (!pedidoResponse.ok) {
        throw new Error(
          pedidoData.detail ||
            'Não foi possível registrar o pedido.'
        );
      }

      const pedidoId = pedidoData.pedido?.id;

      if (!pedidoId) {
        throw new Error(
          'O backend não retornou o número do pedido.'
        );
      }

      const pagamentoResponse = await fetch(
        `${API_URL}/api/pagamentos/pedido/${pedidoId}`,
        {
          method: 'POST',
        }
      );

      const pagamentoData = await pagamentoResponse.json();

      if (!pagamentoResponse.ok) {
        throw new Error(
          pagamentoData.detail ||
            'Não foi possível criar o checkout.'
        );
      }

      if (!pagamentoData.link_pagamento) {
        console.error('Resposta do checkout:', pagamentoData);

        throw new Error(
          'O backend não retornou o link de pagamento esperado.'
        );
      }

      window.location.href = pagamentoData.link_pagamento;
    } catch (error) {
      console.error('Erro ao iniciar compra:', error);

      alert(
        error.message ||
          'Erro ao iniciar a compra. Verifique se o backend está funcionando.'
      );
    } finally {
      setLoading(false);
    }  
  }
  if (
    window.location.pathname.replace(/\/$/, '') === '/validar-ingressos'
  ) {
    return <ValidarIngressos />;
  }

  return (
    <main className="page">
      <nav className="nav">
        <div className="brand">
          <Sparkles size={20} /> CRISTOTECA{' '}
          <span>TODOS OS SANTOS</span>
        </div>

        <a className="nav-link" href="#ingressos">
          Comprar ingresso
        </a>
      </nav>

      <section className="hero">
        <div className="glow glow-one" />
        <div className="glow glow-two" />

        <div className="hero-content">
          <div className="eyebrow">
            <span /> UMA NOITE DE FÉ, MÚSICA E COMUNHÃO <span />
          </div>

          <h1>
            CRISTO<span>TECA</span>
          </h1>

          <div className="subtitle">TODOS OS SANTOS</div>

          <p className="hero-copy">
            Uma noite especial para celebrar a fé com música,
            alegria e comunhão.
          </p>

          <div className="hero-tags">
            <span>
              <Music2 size={16} /> Apresentações musicais
            </span>
            <span>
              <Sparkles size={16} /> Concurso de fantasia
            </span>
          </div>

          <a className="primary-btn" href="#ingressos">
            <Ticket size={19} /> GARANTA SEU INGRESSO
          </a>
        </div>

        <div className="disco" aria-hidden="true">
          <div />
        </div>
      </section>

      <section className="details">
        <article className="detail">
          <CalendarDays />
          <div>
            <small>DATA</small>
            <strong>31 OUT 2026</strong>
            <span>Sábado</span>
          </div>
        </article>

        <article className="detail">
          <Clock3 />
          <div>
            <small>HORÁRIO</small>
            <strong>19h</strong>
            <span>Abertura do evento</span>
          </div>
        </article>

        <article className="detail">
          <MapPin />
          <div>
            <small>LOCAL</small>
            <strong>Rua Capri, 53</strong>
            <span>Jardim Santa Emília</span>
          </div>
        </article>
      </section>

      <section className="experience">
        <div className="section-heading">
          <small>PREPARE O SEU LOOK</small>
          <h2>Uma festa para celebrar</h2>
          <p>
            Venha com uma fantasia inspirada exclusivamente em
            um santo da Igreja Católica e participe do nosso
            concurso.
          </p>
        </div>

        <div className="perks">
          <article>
            <Music2 />
            <h3>Música</h3>
            <p>Apresentações musicais para celebrar juntos.</p>
          </article>

          <article>
            <Utensils />
            <h3>Lanches</h3>
            <p>Opções deliciosas para curtir a noite.</p>
          </article>

          <article>
            <Martini />
            <h3>Drinks sem álcool</h3>
            <p>Bebidas não alcoólicas para todos aproveitarem.</p>
          </article>
        </div>
      </section>

      <section className="buy-section" id="ingressos">
        {restoringOrder ? (
  <div className="buy-card payment-message">
    <RefreshCw size={32} />
    <h2>Recuperando seu ingresso...</h2>
    <p>Estamos verificando seu pedido. Aguarde um instante.</p>
  </div>
) : paymentResult ? (
  <div className="buy-card payment-message">
    <CheckCircle size={48} />

            <h2>Pagamento confirmado!</h2>

            <p>
              Seu pagamento foi aprovado e seus ingressos
              estão liberados.
            </p>

            <div className="total">
              <span>Ingressos liberados</span>
              <strong>
                {paymentResult.quantidade_ingressos}
              </strong>
            </div>

            <a
              className="primary-btn checkout"
              href={`${API_URL}/api/ingressos/pedido/${paymentResult.pedido_id}/pdf`}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={19} />
              ABRIR / BAIXAR MEUS INGRESSOS
            </a>

            <p className="fineprint">
              Salve o PDF e apresente o QR Code de cada
              ingresso na entrada do evento.
            </p>
          </div>
        ) : (
          <>
            {checkingPayment && (
              <div className="buy-card payment-message">
                <RefreshCw size={32} />
                <h2>Verificando seu pagamento...</h2>
                <p>
                  Estamos consultando o Mercado Pago.
                  Aguarde alguns instantes.
                </p>
              </div>
            )}

            {paymentError && (
              <div className="buy-card payment-message">
                <AlertCircle size={36} />

                <h2>Pagamento ainda não confirmado</h2>

                <p>{paymentError}</p>

                {returnedOrderId && (
                  <button
                    className="primary-btn checkout"
                    type="button"
                    disabled={checkingPayment}
                    onClick={() => verifyPayment(returnedOrderId)}
                  >
                    <RefreshCw size={18} />
                    {checkingPayment
                      ? 'CONSULTANDO...'
                      : 'VERIFICAR PAGAMENTO NOVAMENTE'}
                  </button>
                )}
              </div>
            )}

            <div className="buy-copy">
              <small>1º LOTE</small>
              <h2>Seu lugar nessa noite.</h2>
              <p>Ingresso individual por apenas</p>
              <div className="price">{money(PRICE_CENTS)}</div>
              <div className="secure">
                <ShieldCheck size={17} />
                Pagamento seguro pelo Mercado Pago
              </div>
            </div>

            <form className="buy-card" onSubmit={startPurchase}>
              <div className="ticket-icon">
                <Ticket size={27} />
                <div>
                  <strong>Ingresso da Cristoteca</strong>
                  <small>Todos os Santos · 1º lote</small>
                </div>
              </div>

              <div className="qty-row">
                <div>
                  <strong>Quantidade</strong>
                  <small>Escolha quantos ingressos deseja</small>
                </div>

                <div className="stepper">
                  <button
                    type="button"
                    aria-label="Diminuir quantidade"
                    onClick={() =>
                      setQuantity((q) => Math.max(1, q - 1))
                    }
                  >
                    <Minus size={16} />
                  </button>

                  <strong>{quantity}</strong>

                  <button
                    type="button"
                    aria-label="Aumentar quantidade"
                    onClick={() =>
                      setQuantity((q) => Math.min(20, q + 1))
                    }
                  >
                    <Plus size={16} />
                  </button>
                </div>
              </div>

              <div className="form-fields">
                <label htmlFor="buyer-name">Nome completo</label>
                <input
                  id="buyer-name"
                  type="text"
                  placeholder="Digite seu nome completo"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  minLength={2}
                  maxLength={120}
                  required
                />

                <label htmlFor="buyer-email">E-mail</label>
                <input
                  id="buyer-email"
                  type="email"
                  placeholder="seuemail@exemplo.com"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  maxLength={254}
                  required
                />

                <label htmlFor="buyer-phone">
                  Telefone (opcional)
                </label>
                <input
                  id="buyer-phone"
                  type="tel"
                  placeholder="(11) 99999-9999"
                  autoComplete="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  maxLength={30}
                />
              </div>

              <div className="total">
                <span>Total</span>
                <strong>{money(quantity * PRICE_CENTS)}</strong>
              </div>

              <button
                className="primary-btn checkout"
                type="submit"
                disabled={loading}
              >
                {loading
                  ? 'PREPARANDO PAGAMENTO...'
                  : 'CONTINUAR PARA PAGAMENTO'}
                {!loading && <span> →</span>}
              </button>

              <p className="fineprint">
                O ingresso será liberado após a confirmação do
                pagamento. Limite de 20 ingressos por pedido.
              </p>
            </form>
          </>
        )}
      </section>

      <footer>
        <div className="brand">
          <Sparkles size={18} /> CRISTOTECA{' '}
          <span>TODOS OS SANTOS</span>
        </div>

        <p>31 de outubro de 2026 · 19h</p>
        <small>
          Pagamento e liberação dos ingressos sujeitos à
          confirmação pelo sistema.
        </small>
      </footer>
    </main>
  );
}
