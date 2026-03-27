from sqlalchemy.orm import Session, joinedload

from models.conta_meta import ContaMetaEntity
from models.assinatura import AssinaturaEntity


class ContaMetaService:

    @staticmethod
    def get_by_ig_account_id(db: Session, ig_account_id: str):
        return (
            db.query(ContaMetaEntity)
            .filter(ContaMetaEntity.ig_account_id == ig_account_id)
            .first()
        )

    @staticmethod
    def get_contas_by_user_id(db: Session, user_id: str):
        return (
            db.query(ContaMetaEntity)
            .options(joinedload(ContaMetaEntity.assinatura))
            .filter(ContaMetaEntity.user_id == user_id)
            .all()
        )

    @staticmethod
    def get_conta_by_id_and_user_id(db: Session, conta_meta_id: int, user_id: str):
        return (
            db.query(ContaMetaEntity)
            .options(joinedload(ContaMetaEntity.assinatura))
            .filter(
                ContaMetaEntity.id == conta_meta_id,
                ContaMetaEntity.user_id == user_id
            )
            .first()
        )

    @staticmethod
    def create_conta_meta(db: Session, user_id: str, ig_account_id: str, long_lived_token: str):
        conta = ContaMetaEntity(
            user_id=user_id,
            ig_account_id=ig_account_id,
            long_lived_token=long_lived_token
        )

        db.add(conta)
        db.commit()
        db.refresh(conta)

        assinatura = AssinaturaEntity(
            conta_meta_id=conta.id,
            plano="free",
            status="active"
        )

        db.add(assinatura)
        db.commit()
        db.refresh(assinatura)

        return conta