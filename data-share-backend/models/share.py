from sqlalchemy import BigInteger, String, Text, Boolean, Integer, Column, ForeignKey
from db import database

class Share(database.Model):
    __tablename__ = 'share_datasets'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    consumer_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    dataset_id = Column(BigInteger, ForeignKey('datasets.id'), nullable=False)
    request_description = Column(Text, nullable=False, default="无")
    is_shared = Column(Boolean, nullable=False, default=False)        # 是否上架公开
