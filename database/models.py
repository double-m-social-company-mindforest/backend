from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base
import enum


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
    image_filename = Column(Text)
    image_filename_right = Column(Text)
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


class CounselingField(Base):
    """상담 분야 테이블"""
    __tablename__ = "counseling_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # general, family, couple 등
    name = Column(String(100), nullable=False)  # 한글명
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    """Refresh Token 관리 테이블"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    counselor_id = Column(Integer, ForeignKey("counselors.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    counselor = relationship("Counselor")


class ConsultationStatus(str, enum.Enum):
    waiting = "waiting"
    active = "active"
    completed = "completed"
    terminated = "terminated"


class MessageType(str, enum.Enum):
    text = "text"
    system = "system"
    image = "image"


class SenderType(str, enum.Enum):
    user = "user"
    counselor = "counselor"


class Consultation(Base):
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_code = Column(String(9), unique=True, nullable=False, index=True)
    user_nickname = Column(String(100), nullable=False)
    character_type_id = Column(Integer, ForeignKey("final_types.id"), nullable=False)
    character_name = Column(String(100), nullable=False)
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.waiting)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_card_issued = Column(Boolean, default=False)
    
    counselor_id = Column(Integer, ForeignKey("counselors.id"), nullable=True)
    
    # 관계 설정
    character_type = relationship("FinalType")
    counselor = relationship("Counselor", back_populates="consultations")
    messages = relationship("ConsultationMessage", back_populates="consultation", cascade="all, delete-orphan")
    card = relationship("ConsultationCard", back_populates="consultation", uselist=False)


class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_type = Column(Enum(MessageType), default=MessageType.text)
    
    # 관계 설정
    consultation = relationship("Consultation", back_populates="messages")


class ConsultationCard(Base):
    __tablename__ = "consultation_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), unique=True, nullable=False)
    card_data = Column(JSON, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    consultation = relationship("Consultation", back_populates="card")


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class CounselorStatus(str, enum.Enum):
    offline = "offline"
    online = "online"
    busy = "busy"
    away = "away"
    waiting_for_call = "waiting_for_call"  # 콜대기 상태


class Counselor(Base):
    __tablename__ = "counselors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 기본 정보
    username = Column(String(50), unique=True, nullable=False, index=True)  # 아이디
    password_hash = Column(String(255), nullable=False)  # 해시된 비밀번호
    name = Column(String(100), nullable=False)  # 실명
    gender = Column(Enum(Gender), nullable=False)  # 성별
    birth_date = Column(String(10), nullable=False)  # 생년월일 (YYYY-MM-DD)
    phone = Column(String(20), unique=True, nullable=False, index=True)  # 휴대폰 번호
    email = Column(String(255), unique=True, nullable=True, index=True)  # 이메일 (선택)
    
    # 상담 관련
    counseling_fields = Column(JSON, nullable=False)  # 상담 분야 ID 리스트
    
    # 계정 관리
    is_approved = Column(Boolean, default=False)  # 관리자 승인 여부
    approved_at = Column(DateTime(timezone=True), nullable=True)  # 승인 일시
    approved_by = Column(Integer, nullable=True)  # 승인한 관리자 ID
    
    # 시스템 필드
    status = Column(Enum(CounselorStatus), default=CounselorStatus.offline)
    max_concurrent_sessions = Column(Integer, default=3)  # 동시 상담 가능 수
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계 설정
    consultations = relationship("Consultation", back_populates="counselor")



class ConsultationRequest(Base):
    __tablename__ = "consultation_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("counselors.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, accepted, rejected, expired
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    response_message = Column(Text, nullable=True)
    
    # 관계 설정
    consultation = relationship("Consultation")
    counselor = relationship("Counselor")