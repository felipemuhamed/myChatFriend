from fastapi import HTTPException
from models.automacao import AutomacaoCreateSchema, AutomacaoEntity
from models.meta import ContaMetaEntity, MetaTokenUpdateSchema
from sqlalchemy.orm import  Session

class AutomacaoService:
    """Classe que concentra toda a lógica de negócio e manipulação do banco"""
    def __init__(self, db: Session):
        self.db = db

    def salvar_token(self, user_id: str, dados: MetaTokenUpdateSchema):
        # Busca se a conta já existe
        conta = self.db.query(ContaMetaEntity).filter(ContaMetaEntity.ig_account_id == dados.ig_account_id).first()
        
        if conta:
            # Atualiza o token se a conta já existir
            conta.long_lived_token = dados.long_lived_token
            conta.user_id = user_id
        else:
            # Cria uma nova conta
            conta = ContaMetaEntity(
                user_id=user_id, 
                ig_account_id=dados.ig_account_id, 
                long_lived_token=dados.long_lived_token
            )
            self.db.add(conta)
        
        self.db.commit()
        return conta

    def criar_nova_automacao(self, user_id: str, dados: AutomacaoCreateSchema):
        # Confirma se o usuário é o dono daquela conta do Instagram
        conta = self.db.query(ContaMetaEntity).filter(
            ContaMetaEntity.ig_account_id == dados.ig_account_id,
            ContaMetaEntity.user_id == user_id
        ).first()

        if not conta:
            raise HTTPException(status_code=404, detail="Conta do Instagram não encontrada ou não pertence a este usuário.")

        nova_automacao = AutomacaoEntity(
            conta_id=conta.id,
            palavra_chave=dados.palavra_chave.lower().strip(),
            mensagem_resposta=dados.mensagem_resposta
        )
        
        self.db.add(nova_automacao)
        self.db.commit()
        return nova_automacao

    def obter_automacoes_do_usuario(self, user_id: str):
        # Retorna todas as automações linkadas às contas daquele usuário do Keycloak
        return self.db.query(AutomacaoEntity).join(ContaMetaEntity).filter(ContaMetaEntity.user_id == user_id).all()