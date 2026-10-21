# Cristoteca Todos os Santos

Starter do projeto: React + Vite no frontend e FastAPI no backend.

## Pré-requisitos
- Node.js LTS
- Python 3.11+
- Git (opcional)

## 1. Iniciar o backend
No terminal, entre na pasta `backend`:

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Instale as dependências e inicie:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
Documentação: http://127.0.0.1:8000/docs

## 2. Iniciar o frontend
Em outro terminal, entre em `frontend`:

```bash
npm install
npm run dev
```

Abra o endereço exibido pelo Vite (normalmente http://localhost:5173).

## 3. Estado atual
Esta é a primeira etapa: página do evento e API mínima para testar a estrutura. O botão de compra ainda não cobra dinheiro e não emite ingresso válido. Não anuncie nem utilize em produção até concluir Mercado Pago, banco de dados, webhooks e validação autenticada.

## Próximas etapas
1. Supabase/PostgreSQL: pedidos, pagamentos e ingressos.
2. Mercado Pago Checkout Pro: criar preferência no backend.
3. Webhook: confirmar o pagamento no servidor e emitir os ingressos.
4. PDF individual com QR Code aleatório e não previsível.
5. Tela de leitura/validação, com marcação atômica de ingresso utilizado.
6. Publicação com HTTPS, variáveis de ambiente e testes de ponta a ponta.
