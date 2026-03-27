import os
import requests
from celery import Celery
from database.db import DatabaseConfig

import models
from models import ContaMetaEntity, AutomacaoEntity

# Conecta o Trabalhador à fila do RabbitMQ
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://admin:admin123@rabbitmq:5672//")
celery_app = Celery("saas_worker", broker=BROKER_URL)

API_VERSION = 'v25.0' 
db_config = DatabaseConfig()

# ==========================================
# A TAREFA EM SEGUNDO PLANO (Background Job)
# ==========================================
@celery_app.task(name="worker.processar_evento_meta", bind=True, max_retries=3)
def processar_evento_meta(self, payload):
    db = db_config.SessionLocal() 
    
    try:
        for entry in payload.get('entry', []):
            ig_account_id = entry.get('id')
            
            # ==============================================================
            # 📩 BLOCO 1: LENDO MENSAGENS DIRETAS (DMs)
            # ==============================================================
            if 'messaging' in entry:
                for event in entry['messaging']:
                    sender_id = event.get('sender', {}).get('id')
                    message_data = event.get('message', {})
                    message_text = message_data.get('text', '').strip().lower()
                    
                    if message_data.get('is_echo'):
                        continue

                    if message_text:
                        print(f"📩 Nova DM na conta {ig_account_id}: '{message_text}'")

                        conta_cliente = db.query(ContaMetaEntity).filter(
                            ContaMetaEntity.ig_account_id == ig_account_id
                        ).first()

                        if not conta_cliente:
                            print(f"⚠️ Conta {ig_account_id} não cadastrada no SaaS. Ignorando DM.")
                            continue

                        for regra in conta_cliente.automacoes:
                            if not regra.ativa:
                                continue                            

                            palavra_chave_limpa = regra.palavra_chave.strip().lower()

                            if palavra_chave_limpa in message_text:
                                print(f"🚀 Gatilho '{palavra_chave_limpa}' acionado! Enviando DM para {sender_id}...")
                                
                                enviar_dm(
                                    recipient_id=sender_id, 
                                    ig_account_id=conta_cliente.ig_account_id, 
                                    mensagem=regra.mensagem_resposta, 
                                    access_token=conta_cliente.long_lived_token
                                )
                                break 

            # ==============================================================
            # 💬 BLOCO 2: LENDO COMENTÁRIOS (Reels e Posts)
            # ==============================================================
            if 'changes' in entry:
                for change in entry['changes']:
                    if change.get('field') == 'comments':
                        valor = change.get('value', {})
                        
                        comment_id = valor.get('id')
                        username = valor.get('from', {}).get('username')
                        message_text = valor.get('text', '').strip().lower()

                        if message_text:
                            print(f"💬 Novo Comentário de @{username} na conta {ig_account_id}: '{message_text}'")

                            # Busca o cliente no banco de dados
                            conta_cliente = db.query(ContaMetaEntity).filter(
                                ContaMetaEntity.ig_account_id == ig_account_id
                            ).first()

                            if not conta_cliente:
                                print(f"⚠️ Conta {ig_account_id} não cadastrada no SaaS. Ignorando comentário.")
                                continue

                            # Varre as regras de automação
                            for regra in conta_cliente.automacoes:
                                if not regra.ativa:
                                    continue                            

                                palavra_chave_limpa = regra.palavra_chave.strip().lower()

                                if palavra_chave_limpa in message_text:
                                    print(f"🚀 Gatilho '{palavra_chave_limpa}' acionado! Chamando @{username} na DM...")
                                    
                                    # Usa a função específica para comentários
                                    enviar_dm_por_comentario(
                                        comment_id=comment_id, 
                                        ig_account_id=conta_cliente.ig_account_id, 
                                        mensagem=regra.mensagem_resposta, 
                                        access_token=conta_cliente.long_lived_token
                                    )
                                    break 

    except Exception as e:
        print(f"❌ Erro inesperado no worker: {e}")
        self.retry(exc=e, countdown=60) 
        
    finally:
        db.close()

# ==========================================
# FUNÇÕES DE ENVIO DA META API
# ==========================================

# 1. Função original para responder DMs
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


# 2. Nova função para enviar DM baseada em um Comentário
def enviar_dm_por_comentario(comment_id, ig_account_id, mensagem, access_token):
    url = f"https://graph.instagram.com/{API_VERSION}/{ig_account_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # ⚠️ A principal diferença: usamos "comment_id" no recipient
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": mensagem}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ DM enviada com sucesso para o autor do comentário {comment_id}!")
        else:
            print(f"❌ Erro da Meta ao responder comentário: {response.json()}")
    except Exception as e:
        print(f"❌ Falha de conexão na requisição: {e}")