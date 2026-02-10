from sqlalchemy import BigInteger, Column, ForeignKey
from db import database

class DownloadLog(database.Model):
    __tablename__ = 'download_logs'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    dataset_id = Column(BigInteger, ForeignKey('datasets.id'), nullable=False)
