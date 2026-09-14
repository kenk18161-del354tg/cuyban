from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime,
    Integer, String, Text
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    tg_id      = Column(BigInteger, unique=True, nullable=False, index=True)
    username   = Column(String(64), nullable=True)
    full_name  = Column(String(128), nullable=True)
    credits    = Column(Integer, default=0, nullable=False)
    is_banned  = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<User tg_id={self.tg_id} credits={self.credits}>'


class Order(Base):
    __tablename__ = 'orders'

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_tg_id     = Column(BigInteger, nullable=False, index=True)
    service        = Column(String(32), nullable=False)   # bcp, agr, ibk...
    data           = Column(String(256), nullable=False)  # dato enviado por el usuario
    price          = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after  = Column(Integer, nullable=False)
    status         = Column(String(16), default='PENDIENTE', nullable=False)
    # estados: PENDIENTE | PROCESANDO | COMPLETADO | CANCELADO
    result_data    = Column(Text, nullable=True)          # datos del resultado final
    group_msg_id   = Column(BigInteger, nullable=True)    # msg en SOLICITANDES
    client_msg_id  = Column(BigInteger, nullable=True)    # msg de progreso al cliente
    group_chat_id  = Column(BigInteger, nullable=True)    # chat_id del grupo
    original_msg_id = Column(BigInteger, nullable=True)   # msg original solicitud
    ask_msg_id     = Column(BigInteger, nullable=True)    # msg pidiendo datos
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at     = Column(DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Order id={self.id} service={self.service} status={self.status}>'


class Payment(Base):
    __tablename__ = 'payments'

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_tg_id     = Column(BigInteger, nullable=False, index=True)
    username       = Column(String(64), nullable=True)
    full_name      = Column(String(128), nullable=True)
    pack           = Column(String(16), nullable=False)   # basico | plus | pro
    credits        = Column(Integer, nullable=False)
    bonus          = Column(Integer, nullable=False, default=0)
    price_soles    = Column(Integer, nullable=False)
    status         = Column(String(16), default='PENDIENTE', nullable=False)
    # estados: PENDIENTE | APROBADO | RECHAZADO
    photo_file_id  = Column(String(256), nullable=True)   # file_id comprobante
    group_msg_id   = Column(BigInteger, nullable=True)    # msg en grupo PAGOS
    qr_msg_id      = Column(BigInteger, nullable=True)    # msg QR al cliente
    instructions_msg_id = Column(BigInteger, nullable=True)  # msg instrucciones
    confirm_msg_id = Column(BigInteger, nullable=True)    # msg "comprobante recibido"
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Payment id={self.id} pack={self.pack} status={self.status}>'
