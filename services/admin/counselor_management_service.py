from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from database.models import Counselor, CounselorStatus, Admin
from schemas.admin.counselor_management import (
    CounselorPendingApproval,
    CounselorApprovalRequest,
    CounselorApprovalResponse,
    CounselorListItem,
    CounselorListRequest,
    CounselorListResponse,
    CounselorDetailResponse,
    CounselorStatusUpdateRequest,
    CounselorStatsResponse
)

logger = logging.getLogger(__name__)


class CounselorManagementService:
    """상담사 관리 서비스"""
    
    @staticmethod
    def get_pending_approvals(db: Session) -> List[CounselorPendingApproval]:
        """승인 대기 중인 상담사 목록 조회"""
        try:
            counselors = db.query(Counselor).filter(
                and_(
                    Counselor.is_approved == False,
                    Counselor.is_active == True
                )
            ).order_by(desc(Counselor.created_at)).all()
            
            return [CounselorPendingApproval.from_orm(counselor) for counselor in counselors]
            
        except Exception as e:
            logger.error(f"승인 대기 상담사 조회 중 오류: {e}")
            raise HTTPException(status_code=500, detail="승인 대기 상담사 조회 중 오류가 발생했습니다")
    
    @staticmethod
    def approve_counselor(
        db: Session, 
        counselor_id: int, 
        admin_id: int, 
        action: str,
        rejection_reason: Optional[str] = None
    ) -> CounselorApprovalResponse:
        """상담사 승인/거절 처리"""
        try:
            # 상담사 조회
            counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
            if not counselor:
                raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
            
            # 이미 처리된 상담사인지 확인
            if counselor.is_approved and action == "approve":
                return CounselorApprovalResponse(
                    counselor_id=counselor_id,
                    action=action,
                    success=False,
                    message="이미 승인된 상담사입니다"
                )
            
            if action == "approve":
                # 승인 처리
                counselor.is_approved = True
                counselor.approved_at = datetime.utcnow()
                counselor.approved_by = admin_id
                
                db.commit()
                
                logger.info(f"상담사 승인 완료: counselor_id={counselor_id}, admin_id={admin_id}")
                
                return CounselorApprovalResponse(
                    counselor_id=counselor_id,
                    action=action,
                    success=True,
                    message=f"상담사 '{counselor.name}' 계정이 승인되었습니다"
                )
            
            elif action == "reject":
                # 거절 처리 (계정 비활성화)
                counselor.is_active = False
                counselor.approved_by = admin_id
                
                # 거절 사유는 별도 테이블이나 로그로 관리할 수 있음
                # 현재는 로그로만 기록
                logger.info(f"상담사 거절: counselor_id={counselor_id}, admin_id={admin_id}, reason={rejection_reason}")
                
                db.commit()
                
                return CounselorApprovalResponse(
                    counselor_id=counselor_id,
                    action=action,
                    success=True,
                    message=f"상담사 '{counselor.name}' 계정이 거절되었습니다"
                )
            
            else:
                raise HTTPException(status_code=400, detail="올바르지 않은 액션입니다")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"상담사 승인/거절 처리 중 오류: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="승인/거절 처리 중 오류가 발생했습니다")
    
    @staticmethod
    def get_counselor_list(db: Session, request: CounselorListRequest) -> CounselorListResponse:
        """상담사 목록 조회 (필터링, 검색, 페이징 지원)"""
        try:
            query = db.query(Counselor)
            
            # 상태 필터 적용
            if request.status_filter:
                if request.status_filter == "pending":
                    query = query.filter(and_(
                        Counselor.is_approved == False,
                        Counselor.is_active == True
                    ))
                elif request.status_filter == "approved":
                    query = query.filter(Counselor.is_approved == True)
                elif request.status_filter == "rejected":
                    query = query.filter(and_(
                        Counselor.is_approved == False,
                        Counselor.is_active == False
                    ))
                # "all"인 경우 필터 적용하지 않음
            
            # 검색 조건 적용
            if request.search:
                search_term = f"%{request.search}%"
                query = query.filter(or_(
                    Counselor.name.ilike(search_term),
                    Counselor.username.ilike(search_term),
                    Counselor.phone.ilike(search_term),
                    Counselor.email.ilike(search_term)
                ))
            
            # 전체 개수 조회
            total = query.count()
            
            # 페이징 적용
            offset = (request.page - 1) * request.size
            counselors = query.order_by(desc(Counselor.created_at)).offset(offset).limit(request.size).all()
            
            # 총 페이지 수 계산
            total_pages = (total + request.size - 1) // request.size
            
            return CounselorListResponse(
                counselors=[CounselorListItem.from_orm(counselor) for counselor in counselors],
                total=total,
                page=request.page,
                size=request.size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"상담사 목록 조회 중 오류: {e}")
            raise HTTPException(status_code=500, detail="상담사 목록 조회 중 오류가 발생했습니다")
    
    @staticmethod
    def get_counselor_detail(db: Session, counselor_id: int) -> CounselorDetailResponse:
        """상담사 상세 정보 조회"""
        try:
            counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
            if not counselor:
                raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
            
            return CounselorDetailResponse.from_orm(counselor)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"상담사 상세 정보 조회 중 오류: {e}")
            raise HTTPException(status_code=500, detail="상담사 상세 정보 조회 중 오류가 발생했습니다")
    
    @staticmethod
    def update_counselor_status(
        db: Session, 
        request: CounselorStatusUpdateRequest, 
        admin_id: int
    ) -> Dict[str, Any]:
        """상담사 활성화/비활성화 상태 변경"""
        try:
            counselor = db.query(Counselor).filter(Counselor.id == request.counselor_id).first()
            if not counselor:
                raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
            
            old_status = counselor.is_active
            counselor.is_active = request.is_active
            
            db.commit()
            
            action = "활성화" if request.is_active else "비활성화"
            logger.info(f"상담사 상태 변경: counselor_id={request.counselor_id}, admin_id={admin_id}, {action}")
            
            return {
                "counselor_id": request.counselor_id,
                "old_status": old_status,
                "new_status": request.is_active,
                "message": f"상담사 '{counselor.name}' 계정이 {action}되었습니다"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"상담사 상태 변경 중 오류: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="상담사 상태 변경 중 오류가 발생했습니다")
    
    @staticmethod
    def get_counselor_stats(db: Session) -> CounselorStatsResponse:
        """상담사 통계 정보 조회"""
        try:
            # 전체 상담사 수
            total_counselors = db.query(func.count(Counselor.id)).scalar()
            
            # 승인 대기 중인 상담사 수
            pending_approval = db.query(func.count(Counselor.id)).filter(
                and_(
                    Counselor.is_approved == False,
                    Counselor.is_active == True
                )
            ).scalar()
            
            # 승인된 상담사 수
            approved_counselors = db.query(func.count(Counselor.id)).filter(
                Counselor.is_approved == True
            ).scalar()
            
            # 활성화된 상담사 수
            active_counselors = db.query(func.count(Counselor.id)).filter(
                and_(
                    Counselor.is_active == True,
                    Counselor.is_approved == True
                )
            ).scalar()
            
            # 온라인 상담사 수
            online_counselors = db.query(func.count(Counselor.id)).filter(
                and_(
                    Counselor.is_active == True,
                    Counselor.is_approved == True,
                    Counselor.status.in_([CounselorStatus.online, CounselorStatus.waiting_for_call])
                )
            ).scalar()
            
            return CounselorStatsResponse(
                total_counselors=total_counselors or 0,
                pending_approval=pending_approval or 0,
                approved_counselors=approved_counselors or 0,
                active_counselors=active_counselors or 0,
                online_counselors=online_counselors or 0
            )
            
        except Exception as e:
            logger.error(f"상담사 통계 조회 중 오류: {e}")
            raise HTTPException(status_code=500, detail="상담사 통계 조회 중 오류가 발생했습니다")
    
    @staticmethod
    def bulk_approve_counselors(
        db: Session, 
        counselor_ids: List[int], 
        admin_id: int
    ) -> Dict[str, Any]:
        """상담사 일괄 승인"""
        try:
            # 승인 대기 중인 상담사들만 필터링
            counselors = db.query(Counselor).filter(
                and_(
                    Counselor.id.in_(counselor_ids),
                    Counselor.is_approved == False,
                    Counselor.is_active == True
                )
            ).all()
            
            if not counselors:
                raise HTTPException(status_code=404, detail="승인 가능한 상담사를 찾을 수 없습니다")
            
            # 일괄 승인 처리
            approved_count = 0
            current_time = datetime.utcnow()
            
            for counselor in counselors:
                counselor.is_approved = True
                counselor.approved_at = current_time
                counselor.approved_by = admin_id
                approved_count += 1
            
            db.commit()
            
            logger.info(f"상담사 일괄 승인 완료: count={approved_count}, admin_id={admin_id}")
            
            return {
                "approved_count": approved_count,
                "requested_count": len(counselor_ids),
                "message": f"{approved_count}명의 상담사가 승인되었습니다"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"상담사 일괄 승인 중 오류: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="일괄 승인 처리 중 오류가 발생했습니다")