from auth.handler import AuthHandler
from database.db import DatabaseConfig
from fastapi import FastAPI, Depends, status, Request, Response
from models.automacao import AutomacaoCreateSchema
from models.meta import MetaTokenUpdateSchema
from service.automacao_service import AutomacaoService
from worker import processar_evento_meta 
from sqlalchemy.orm import  Session



VERIFY_TOKEN = "minha_senha_super_secreta_saas_123" 
app = FastAPI(title="SaaS Bot Automação - Orientado a Objetos")
db_config = DatabaseConfig()

@app.post("/api/meta/token")
def endpoint_salvar_token(
    dados: MetaTokenUpdateSchema, 
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    servico.salvar_token(user_id, dados)
    return {"status": "sucesso", "msg": "Token da Meta atualizado com sucesso"}

@app.post("/api/automacoes")
def endpoint_criar_automacao(
    dados: AutomacaoCreateSchema, 
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    automacao = servico.criar_nova_automacao(user_id, dados)
    return {"status": "sucesso", "msg": "Automação criada!", "id_automacao": automacao.id}

@app.get("/api/automacoes")
def endpoint_listar_automacoes(
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    automacoes = servico.obter_automacoes_do_usuario(user_id)
    return {"automacoes": automacoes}

# ==========================================
# 1. VERIFICAÇÃO (Rota GET)
# A Meta bate aqui uma vez só para checar se o servidor é seu.
# ==========================================
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado pela Meta com sucesso!")
        # A Meta exige que a resposta seja em texto puro (o 'challenge')
        return Response(content=challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    
    return Response(content="Token de verificação inválido", status_code=status.HTTP_403_FORBIDDEN)

# ==========================================
# 2. RECEBIMENTO DE EVENTOS (Rota POST)
# Onde a Meta joga milhares de comentários/DMs
# ==========================================
@app.post("/webhook")
async def handle_webhook(request: Request):
    # Pega o pacote JSON que a Meta enviou
    payload = await request.json()
    
    # Verifica se o evento veio mesmo do Instagram
    if payload.get("object") == "instagram":
        
        # A MÁGICA ACONTECE AQUI:
        # Em vez de ler a mensagem e mandar a DM por aqui, nós usamos o ".delay()".
        # Isso arremessa o JSON inteiro para a memória RAM (Fila do RabbitMQ) 
        # e libera a API imediatamente para receber o próximo cliente.
        processar_evento_meta.delay(payload)
        
    # Respondemos para a Meta em milissegundos: "Recebido, não se preocupe!"
    return {"status": "ok"}