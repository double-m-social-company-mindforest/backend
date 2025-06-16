from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float
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


class FinalType(Base):
    __tablename__ = "final_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    animal = Column(String(50))
    group_name = Column(String(100))
    one_liner = Column(String(255))
    overview = Column(Text)
    greeting = Column(String(255))
    hashtags = Column(JSON)  
    strengths = Column(JSON) 
    weaknesses = Column(JSON) 
    relationship_style = Column(Text)
    behavior_pattern = Column(Text)
    image_filename = Column(String(255))
    image_filename_right = Column(String(255))
    strength_icons = Column(JSON)  
    weakness_icons = Column(JSON)


class IntermediateType(Base):
    __tablename__ = "intermediate_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    characteristics = Column(Text)
    display_order = Column(Integer, default=0)


class KeywordTypeScore(Base):
    __tablename__ = "keyword_type_scores"
    
    sub_keyword_id = Column(Integer, ForeignKey("sub_keywords.id"), primary_key=True)
    intermediate_type_id = Column(Integer, ForeignKey("intermediate_types.id"), primary_key=True)
    score = Column(Integer, nullable=False)
    
    # 관계 설정
    sub_keyword = relationship("SubKeyword")
    intermediate_type = relationship("IntermediateType")


class TypeCombination(Base):
    __tablename__ = "type_combinations"
    
    primary_type_id = Column(Integer, ForeignKey("intermediate_types.id"), primary_key=True)
    secondary_type_id = Column(Integer, ForeignKey("intermediate_types.id"), primary_key=True)
    final_type_id = Column(Integer, ForeignKey("final_types.id"), nullable=False)
    
    # 관계 설정
    primary_type = relationship("IntermediateType", foreign_keys=[primary_type_id])
    secondary_type = relationship("IntermediateType", foreign_keys=[secondary_type_id])
    final_type = relationship("FinalType")


class CalculationWeight(Base):
    __tablename__ = "calculation_weights"
    
    selection_order = Column(Integer, primary_key=True)  # 1, 2, 3
    weight = Column(Float, nullable=False)  # 0.4, 0.3, 0.2