
import { useCallback, useEffect, useRef, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { ArrowLeft, Camera, CheckCircle, ShieldAlert, Ticket } from 'lucide-react';

const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

export default function ValidarIngressos() {
  const [validando, setValidando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState('');
  const [cameraErro, setCameraErro] = useState('');
  const scannerRef = useRef(null);

  const validarCodigo = useCallback(async (codigo) => {
    if (validando || resultado) return;

    setValidando(true);
    setErro('');
    setResultado(null);

    try {
      const response = await fetch(`${API_URL}/api/validacao/validar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo: codigo.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Não foi possível validar o ingresso.');
      }

      setResultado(data);
    } catch (error) {
      setErro(error.message || 'Falha de comunicação com o servidor.');
    } finally {
      setValidando(false);
    }
  }, [validando, resultado]);

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      'leitor-ingresso',
      {
        fps: 10,
        qrbox: { width: 240, height: 240 },
        rememberLastUsedCamera: true,
      },
      false
    );

    scannerRef.current = scanner;

    scanner.render(
      (textoLido) => validarCodigo(textoLido),
      () => {}
    );

    return () => {
      scanner.clear().catch(() => {});
      scannerRef.current = null;
    };
  }, [validarCodigo]);

  const aprovado = resultado?.resultado === 'aprovado';
  const jaUtilizado = resultado?.resultado === 'ja_utilizado';

  return (
    <main style={estilos.pagina}>
      <header style={estilos.topo}>
        <Ticket size={30} />
        <div>
          <strong>CRISTOTECA</strong>
          <div style={{ fontSize: 12, letterSpacing: 2 }}>TODOS OS SANTOS</div>
        </div>
      </header>

      <section style={estilos.cartao}>
        <h1 style={estilos.titulo}>Validar ingresso</h1>
        <p style={estilos.texto}>
          Aponte a câmera para o QR Code apresentado pelo participante.
        </p>

        <div id="leitor-ingresso" />

        {validando && (
          <div style={estilos.aviso}>
            Verificando ingresso...
          </div>
        )}

        {resultado && (
          <div
            role="status"
            style={{
              ...estilos.resultado,
              background: aprovado ? '#dcfce7' : '#fee2e2',
              color: aprovado ? '#166534' : '#991b1b',
            }}
          >
            {aprovado
              ? <CheckCircle size={42} />
              : <ShieldAlert size={42} />}

            <h2 style={{ margin: '10px 0' }}>
              {aprovado
                ? 'INGRESSO VÁLIDO'
                : jaUtilizado
                  ? 'INGRESSO JÁ UTILIZADO'
                  : 'INGRESSO INVÁLIDO'}
            </h2>

            <p style={{ margin: 0 }}>
              {resultado.mensagem || 'Resultado da validação recebido.'}
            </p>

            {resultado.utilizado_em && aprovado && (
              <small>
                Validado em: {new Date(resultado.utilizado_em).toLocaleString('pt-BR')}
              </small>
            )}
          </div>
        )}

        {erro && (
          <div role="alert" style={estilos.erro}>
            <ShieldAlert size={24} />
            <p>{erro}</p>
          </div>
        )}

        {cameraErro && (
          <p role="alert" style={estilos.erro}>{cameraErro}</p>
        )}

        {(resultado || erro) && (
          <button
            type="button"
            style={estilos.botao}
            onClick={() => {
              setResultado(null);
              setErro('');
              setCameraErro('');
            }}
          >
            <Camera size={18} />
            Ler próximo ingresso
          </button>
        )}

        <a href="/" style={estilos.voltar}>
          <ArrowLeft size={16} /> Voltar à página do evento
        </a>
      </section>

      <p style={estilos.rodape}>
        A validação consulta o servidor. Cada ingresso só pode liberar
        a entrada uma vez.
      </p>
    </main>
  );
}

const estilos = {
  pagina: {
    minHeight: '100vh',
    boxSizing: 'border-box',
    padding: '24px 16px',
    background: '#f3f4f6',
    color: '#17251c',
    fontFamily: 'Arial, sans-serif',
  },
  topo: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 28,
    color: '#2a4737',
  },
  cartao: {
    maxWidth: 480,
    margin: '0 auto',
    padding: 22,
    background: '#fff',
    borderRadius: 16,
    boxShadow: '0 4px 20px #00000012',
    textAlign: 'center',
  },
  titulo: { margin: '4px 0 8px', fontSize: 28 },
  texto: { color: '#59645c', lineHeight: 1.5 },
  aviso: {
    padding: 14,
    marginTop: 16,
    background: '#fef3c7',
    borderRadius: 10,
    fontWeight: 'bold',
  },
  resultado: {
    marginTop: 18,
    padding: 20,
    borderRadius: 12,
    overflowWrap: 'anywhere',
  },
  erro: {
    marginTop: 16,
    padding: 14,
    background: '#fee2e2',
    color: '#991b1b',
    borderRadius: 10,
    overflowWrap: 'anywhere',
  },
  botao: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    marginTop: 18,
    padding: 14,
    border: 0,
    borderRadius: 10,
    background: '#2a4737',
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  voltar: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    marginTop: 22,
    color: '#2a4737',
    textDecoration: 'none',
  },
  rodape: {
    maxWidth: 420,
    margin: '20px auto',
    textAlign: 'center',
    color: '#59645c',
    fontSize: 13,
    lineHeight: 1.5,
  },
};
