from sqlalchemy import BigInteger, String, Text, Boolean, Integer, Column, ForeignKey
from db import database

class Dataset(database.Model):
    __tablename__ = 'datasets'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False, default="")
    domain = Column(String(80), nullable=False, default="general")    # 专业领域
    data_type = Column(String(40), nullable=False, default="file")    # 数据类型（csv/sql/json等）
    file_path = Column(String(255), nullable=False)                   # 文件存储路径
    file_size = Column(BigInteger, nullable=False, default=0)
    is_listed = Column(Boolean, nullable=False, default=False)        # 是否上架公开
    downloads = Column(Integer, nullable=False, default=0)            # 下载次数  
    owner_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
