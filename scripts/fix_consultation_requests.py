"""
대기 중인 상담에 대해 상담 요청을 수동으로 생성하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, Consultation, ConsultationRequest, ConsultationStatus, CounselorStatus
from services.counselor.matching_service import MatchingService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_missing_requests():
    """대기 중인 상담에 대해 누락된 요청 생성"""
    db = SessionLocal()
    
    try:
        # 1. 대기 중인 상담 중 요청이 없는 것들 찾기
        waiting_consultations = db.query(Consultation).filter(
            Consultation.status == ConsultationStatus.waiting,
            Consultation.counselor_id.is_(None)
        ).all()
        
        logger.info(f"대기 중인 상담 {len(waiting_consultations)}개 발견")
        
        # 2. 사용 가능한 상담사 찾기
        available_counselor = MatchingService._find_available_counselor(db)
        
        if not available_counselor:
            logger.error("사용 가능한 상담사가 없습니다")
            return
        
        logger.info(f"사용 가능한 상담사: {available_counselor.name} (ID: {available_counselor.id})")
        
        # 3. 각 대기 중인 상담에 대해 요청 생성
        created_count = 0
        for consultation in waiting_consultations:
            # 이미 요청이 있는지 확인
            existing_request = db.query(ConsultationRequest).filter(
                ConsultationRequest.consultation_id == consultation.id
            ).first()
            
            if existing_request:
                logger.info(f"상담 {consultation.consultation_code}에 이미 요청이 존재함 (요청 ID: {existing_request.id})")
                continue
            
            # 새 요청 생성
            try:
                request = MatchingService._create_consultation_request(
                    db, consultation.id, available_counselor.id
                )
                logger.info(f"✅ 상담 {consultation.consultation_code}에 요청 생성 완료 (요청 ID: {request.id})")
                created_count += 1
            except Exception as e:
                logger.error(f"❌ 상담 {consultation.consultation_code} 요청 생성 실패: {e}")
        
        logger.info(f"\n총 {created_count}개의 요청을 생성했습니다.")
        
        # 4. 결과 확인
        logger.info("\n=== 생성 후 상태 확인 ===")
        for consultation in waiting_consultations:
            requests = db.query(ConsultationRequest).filter(
                ConsultationRequest.consultation_id == consultation.id
            ).all()
            
            logger.info(f"상담 {consultation.consultation_code}: 요청 {len(requests)}개")
            for req in requests:
                logger.info(f"  - 요청 ID: {req.id}, 상담사: {req.counselor_id}, 상태: {req.status}")
        
    except Exception as e:
        logger.error(f"요청 생성 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    create_missing_requests()