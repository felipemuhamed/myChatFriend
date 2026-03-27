from auth.handler import AuthHandler
from database.db import DatabaseConfig
from fastapi import FastAPI, Depends, status, Request, Response, HTTPException
from worker import processar_evento_meta 
from sqlalchemy.orm import  Session

from models.assinatura import AssinaturaUpdatePlano
from models.automacao import AutomacaoCreateSchema
from models.meta import ContaMetaCreateRequest, MetaTokenUpdateSchema

from service.assinatura_service import AssinaturaService
from service.automacao_service import AutomacaoService
from service.meta_service import ContaMetaService


VERIFY_TOKEN = "minha_senha_super_secreta_saas_123" 
app = FastAPI(title="SaaS Bot Automação - Orientado a Objetos")
db_config = DatabaseConfig()

@app.on_event("startup")
async def startup_event():
    print("⏳ Iniciando o SaaS...")
    print("Tabelas registradas:", db_config.base.metadata.tables.keys())
    db_config.base.metadata.create_all(bind=db_config.engine)
    print("✅ Banco de dados pronto!")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Desligando o SaaS... Fechando conexões.")

@app.post("/api/conta/token")
async def endpoint_salvar_token(
    dados: MetaTokenUpdateSchema,
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    conta = servico.salvar_token(user_id, dados)

    return {
        "status": "sucesso",
        "msg": "Token da Meta atualizado com sucesso",
        "conta": {
            "id": conta.id,
            "ig_account_id": conta.ig_account_id
        }
    }

# ====================================================================================
@app.get("/api/conta")
def listar_contas_meta(
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    contas = ContaMetaService.get_contas_by_user_id(db=db, user_id=user_id)

    return {
        "contas": [
            {
                "id": conta.id,
                "ig_account_id": conta.ig_account_id,
                "plano": conta.assinatura.plano if conta.assinatura else None,
                "status_assinatura": conta.assinatura.status if conta.assinatura else None
            }
            for conta in contas
        ]
    }

@app.post("/api/conta")
def create_conta_meta(
    payload: ContaMetaCreateRequest,
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    conta = ContaMetaService.create_conta_meta(
        db=db,
        user_id=user_id,
        ig_account_id=payload.ig_account_id,
        long_lived_token=payload.long_lived_token
    )

    return {
        "status": "sucesso",
        "conta": {
            "id": conta.id,
            "user_id": conta.user_id,
            "ig_account_id": conta.ig_account_id,
            "plano": conta.assinatura.plano if conta.assinatura else "free"
        }
    }

@app.get("/api/conta/{conta_meta_id}")
def get_assinatura(conta_meta_id: int, db: Session = Depends(db_config.get_db)):
    assinatura = AssinaturaService.get_by_conta_meta_id(db, conta_meta_id)

    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    return assinatura

@app.put("/api/conta/{conta_meta_id}/plano")
def update_plano(
    conta_meta_id: int,
    payload: AssinaturaUpdatePlano,
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    conta = ContaMetaService.get_conta_by_id_and_user_id(
        db=db,
        conta_meta_id=conta_meta_id,
        user_id=user_id
    )

    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    try:
        assinatura = AssinaturaService.update_plan(
            db=db,
            conta_meta_id=conta_meta_id,
            novo_plano=payload.plano.value if hasattr(payload.plano, "value") else payload.plano
        )
        return assinatura
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ====================================================================================
@app.get("/api/automacoes")
async def endpoint_listar_automacoes(
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    automacoes = servico.obter_automacoes_do_usuario(user_id)

    return {"automacoes": automacoes}

@app.post("/api/automacoes")
async def endpoint_criar_automacao(
    dados: AutomacaoCreateSchema,
    user_id: str = Depends(AuthHandler.get_usuario_logado),
    db: Session = Depends(db_config.get_db)
):
    servico = AutomacaoService(db)
    automacao = servico.criar_nova_automacao(user_id, dados)

    return {
        "status": "sucesso",
        "msg": "Automação criada!",
        "id_automacao": automacao.id
    }
# ====================================================================================



# ====================================================================================
# 1. VERIFICAÇÃO (Rota GET)
# A Meta bate aqui uma vez só para checar se o servidor é seu.
# ====================================================================================
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

# ====================================================================================
# 2. RECEBIMENTO DE EVENTOS (Rota POST)
# Onde a Meta joga milhares de comentários/DMs
# ====================================================================================
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