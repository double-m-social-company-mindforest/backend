from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    
    # 관계 설정
    main_keywords = relationship("MainKeyword", back_populates="category")


class MainKeyword(Base):
    __tablename__ = "main_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    search_volume = Column(Integer, default=0)
    display_order = Column(Integer, default=0)
    
    # 관계 설정
    category = relationship("Category", back_populates="main_keywords")
    sub_keywords = relationship("SubKeyword", back_populates="main_keyword")


class SubKeyword(Base):
    __tablename__ = "sub_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    main_keyword_id = Column(Integer, ForeignKey("main_keywords.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)
    
    # 관계 설정
    main_keyword = relationship("MainKeyword", back_populates="sub_keywords")