from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from models.automacao import AutomacaoEntity, AutomacaoCreateSchema
from models.meta import ContaMetaEntity, MetaTokenUpdateSchema
from models.midia_instagram import MidiaInstagramEntity
from models.automacao_midia import AutomacaoMidiaEntity


class AutomacaoService:
    def __init__(self, db: Session):
        self.db = db

    def salvar_token(self, user_id: str, dados: MetaTokenUpdateSchema):
        conta = (
            self.db.query(ContaMetaEntity)
            .filter(ContaMetaEntity.ig_account_id == dados.ig_account_id)
            .first()
        )

        if conta:
            conta.long_lived_token = dados.long_lived_token
            conta.user_id = user_id
        else:
            conta = ContaMetaEntity(
                user_id=user_id,
                ig_account_id=dados.ig_account_id,
                long_lived_token=dados.long_lived_token
            )
            self.db.add(conta)

        self.db.commit()
        self.db.refresh(conta)
        return conta

    def criar_nova_automacao(self, user_id: str, dados: AutomacaoCreateSchema):
        conta = (
            self.db.query(ContaMetaEntity)
            .filter(
                ContaMetaEntity.ig_account_id == dados.ig_account_id,
                ContaMetaEntity.user_id == user_id
            )
            .first()
        )

        if not conta:
            raise HTTPException(
                status_code=404,
                detail="Conta do Instagram não encontrada ou não pertence a este usuário."
            )

        if not dados.midias:
            raise HTTPException(
                status_code=400,
                detail="É necessário informar ao menos uma mídia para criar a automação."
            )

        nova_automacao = AutomacaoEntity(
            conta_id=conta.id,
            palavra_chave=dados.palavra_chave.lower().strip(),
            mensagem_resposta=dados.mensagem_resposta.strip(),
            ativa=True
        )

        self.db.add(nova_automacao)
        self.db.flush()

        media_ids_recebidos = set()

        for item in dados.midias:
            media_id_normalizado = item.media_id.strip()

            if not media_id_normalizado:
                raise HTTPException(
                    status_code=400,
                    detail="Uma das mídias foi enviada sem media_id."
                )

            if media_id_normalizado in media_ids_recebidos:
                continue

            media_ids_recebidos.add(media_id_normalizado)

            midia = (
                self.db.query(MidiaInstagramEntity)
                .filter(
                    MidiaInstagramEntity.conta_id == conta.id,
                    MidiaInstagramEntity.media_id == media_id_normalizado
                )
                .first()
            )

            if not midia:
                midia = MidiaInstagramEntity(
                    conta_id=conta.id,
                    media_id=media_id_normalizado,
                    media_type=item.media_type,
                    caption=item.caption,
                    permalink=item.permalink,
                    thumbnail_url=item.thumbnail_url,
                    media_url=item.media_url
                )
                self.db.add(midia)
                self.db.flush()
            else:
                # opcional: atualizar metadados se vierem no payload
                midia.media_type = item.media_type or midia.media_type
                midia.caption = item.caption or midia.caption
                midia.permalink = item.permalink or midia.permalink
                midia.thumbnail_url = item.thumbnail_url or midia.thumbnail_url
                midia.media_url = item.media_url or midia.media_url
                self.db.flush()

            vinculo_existente = (
                self.db.query(AutomacaoMidiaEntity)
                .filter(
                    AutomacaoMidiaEntity.automacao_id == nova_automacao.id,
                    AutomacaoMidiaEntity.midia_id == midia.id
                )
                .first()
            )

            if not vinculo_existente:
                vinculo = AutomacaoMidiaEntity(
                    automacao_id=nova_automacao.id,
                    midia_id=midia.id
                )
                self.db.add(vinculo)

        self.db.commit()
        self.db.refresh(nova_automacao)

        return nova_automacao

    def obter_automacoes_do_usuario(self, user_id: str):
        automacoes = (
            self.db.query(AutomacaoEntity)
            .join(ContaMetaEntity, AutomacaoEntity.conta_id == ContaMetaEntity.id)
            .options(
                joinedload(AutomacaoEntity.conta),
                joinedload(AutomacaoEntity.automacao_midias).joinedload(
                    AutomacaoMidiaEntity.midia
                )
            )
            .filter(ContaMetaEntity.user_id == user_id)
            .all()
        )

        return [
            {
                "id": automacao.id,
                "palavra_chave": automacao.palavra_chave,
                "mensagem_resposta": automacao.mensagem_resposta,
                "ativa": automacao.ativa,
                "conta": {
                    "id": automacao.conta.id,
                    "ig_account_id": automacao.conta.ig_account_id
                },
                "midias": [
                    {
                        "id_interno": vinculo.midia.id,
                        "media_id": vinculo.midia.media_id,
                        "media_type": vinculo.midia.media_type,
                        "caption": vinculo.midia.caption,
                        "permalink": vinculo.midia.permalink,
                        "thumbnail_url": vinculo.midia.thumbnail_url,
                        "media_url": vinculo.midia.media_url
                    }
                    for vinculo in automacao.automacao_midias
                ]
            }
            for automacao in automacoes
        ]