import os
import requests
from celery import Celery
from database.db import DatabaseConfig

# ⚠️ IMPORTANTE: Ajuste o caminho dos imports de acordo com a sua pasta de models
from models.meta import ContaMetaEntity 

# Conecta o Trabalhador à fila do RabbitMQ
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://admin:admin123@rabbitmq:5672//")
celery_app = Celery("saas_worker", broker=BROKER_URL)

API_VERSION = 'v19.0' 
db_config = DatabaseConfig()

# ==========================================
# A TAREFA EM SEGUNDO PLANO (Background Job)
# ==========================================
@celery_app.task(name="worker.processar_evento_meta", bind=True, max_retries=3)
def processar_evento_meta(self, payload):
    # O Worker abre a própria sessão com o banco de dados
    # (Assumindo que seu DatabaseConfig tem um SessionLocal ou similar)
    # Se você usa um generator no get_db(), podemos instanciar a sessão diretamente:
    db = db_config.session_local() 
    
    try:
        for entry in payload.get('entry', []):
            ig_account_id = entry.get('id')
            
            if 'messaging' in entry:
                for event in entry['messaging']:
                    sender_id = event.get('sender', {}).get('id')
                    message_data = event.get('message', {})
                    message_text = message_data.get('text', '').strip().lower()
                    
                    # Ignora mensagens do próprio bot
                    if message_data.get('is_echo'):
                        continue

                    if message_text:
                        print(f"📩 Nova DM na conta {ig_account_id}: '{message_text}'")

                        # ==============================================================
                        # 🧠 A INTELIGÊNCIA DO SAAS (Consulta ao Banco)
                        # ==============================================================
                        
                        # 1. Busca o cliente dono desta conta do Instagram
                        conta_cliente = db.query(ContaMetaEntity).filter(
                            ContaMetaEntity.ig_account_id == ig_account_id
                        ).first()

                        # Se a conta não existir no nosso banco, ignoramos
                        if not conta_cliente:
                            print(f"⚠️ Conta {ig_account_id} não cadastrada no SaaS. Ignorando.")
                            continue

                        # 2. Varre as N automações cadastradas por esse cliente
                        # O SQLAlchemy já carrega a lista através do seu `relationship`
                        for regra in conta_cliente.automacoes:

                            if not regra.ativa:
                                continue                            

                            palavra_chave_limpa = regra.palavra_chave.strip().lower()

                            # 3. Verifica se a palavra-chave está na mensagem
                            if palavra_chave_limpa in message_text:
                                print(f"🚀 Gatilho '{palavra_chave_limpa}' acionado! Enviando DM para {sender_id}...")
                                
                                enviar_dm(
                                    recipient_id=sender_id, 
                                    ig_account_id=conta_cliente.ig_account_id, 
                                    mensagem=regra.mensagem_resposta, 
                                    access_token=conta_cliente.long_lived_token
                                )
                                
                                # Interrompe o loop para não enviar mais de uma mensagem
                                # caso o usuário tenha digitado várias palavras-chave na mesma frase
                                break 

    except Exception as e:
        print(f"❌ Erro inesperado no worker: {e}")
        # Opcional: Tenta rodar a tarefa de novo caso o banco de dados tenha piscado
        self.retry(exc=e, countdown=60) 
        
    finally:
        # ISSO É CRÍTICO: Sempre feche a sessão do banco no Celery
        db.close()


# ==========================================
# FUNÇÃO ISOLADA DE ENVIO DA META API
# ==========================================
def enviar_dm(recipient_id, ig_account_id, mensagem, access_token):
    url = f"https://graph.facebook.com/{API_VERSION}/{ig_account_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": mensagem}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ DM enviada com sucesso! (Conta: {ig_account_id})")
        else:
            print(f"❌ Erro da Meta ao enviar DM: {response.json()}")
            
    except Exception as e:
        print(f"❌ Falha de conexão na requisição: {e}")