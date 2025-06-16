from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models import (
    IntermediateType, FinalType, KeywordTypeScore, 
    TypeCombination, CalculationWeight, SubKeyword
)


class TypeCalculationService:
    """유형 계산 및 매핑을 처리하는 DB 기반 서비스 클래스"""

    @classmethod
    def calculate_type_scores_from_db(cls, selected_keyword_ids: Dict[str, List[int]], db: Session, debug: bool = False) -> Dict[int, float]:
        """
        DB에서 키워드별 점수를 조회하여 16개 유형의 점수 계산
        
        Args:
            selected_keyword_ids: {
                "1": [69, 70],      # category_id: [sub_keyword_ids]
                "2": [41],
                "3": [21, 19, 12]
            }
            db: Database session
        
        Returns:
            각 유형별 총점: {1: 8.5, 3: 4.3, ...} (intermediate_type_id: score)
        """
        # 모든 중간 유형 조회
        intermediate_types = db.query(IntermediateType).all()
        type_scores = {type_obj.id: 0.0 for type_obj in intermediate_types}
        
        # 가중치 조회
        weights = {}
        weight_records = db.query(CalculationWeight).all()
        for weight_record in weight_records:
            weights[weight_record.selection_order] = weight_record.weight
        
        # 기본 가중치 설정 (DB에 없는 경우)
        default_weights = {1: 0.4, 2: 0.3, 3: 0.2}
        if not weights:
            weights = default_weights
        
        # 디버깅 정보 저장
        debug_info = {
            "category_details": {},
            "keyword_details": [],
            "weights_used": weights
        }
        
        # 선택된 키워드들로 점수 계산
        for category_id, keyword_ids in selected_keyword_ids.items():
            category_debug = {
                "keyword_scores": [],
                "category_totals": {type_id: 0.0 for type_id in type_scores.keys()}
            }
            
            for idx, keyword_id in enumerate(keyword_ids, 1):
                # 선택 순서에 따른 가중치 적용
                weight = weights.get(idx, 0.0)
                
                # DB에서 해당 키워드의 모든 유형별 점수 조회
                keyword_scores = db.query(KeywordTypeScore).filter(
                    KeywordTypeScore.sub_keyword_id == keyword_id
                ).all()
                
                # 키워드 이름 조회 (디버깅용)
                keyword_name = db.query(SubKeyword).filter(SubKeyword.id == keyword_id).first()
                keyword_name = keyword_name.name if keyword_name else f"ID-{keyword_id}"
                
                keyword_debug = {
                    "keyword_id": keyword_id,
                    "keyword_name": keyword_name,
                    "selection_order": idx,
                    "weight": weight,
                    "raw_scores": {},
                    "weighted_scores": {}
                }
                
                # 각 유형에 가중치 적용하여 점수 추가
                for score_record in keyword_scores:
                    type_id = score_record.intermediate_type_id
                    raw_score = score_record.score
                    weighted_score = raw_score * weight
                    
                    type_scores[type_id] += weighted_score
                    category_debug["category_totals"][type_id] += weighted_score
                    
                    # 디버깅 정보 추가
                    keyword_debug["raw_scores"][type_id] = raw_score
                    keyword_debug["weighted_scores"][type_id] = weighted_score
                
                category_debug["keyword_scores"].append(keyword_debug)
            
            debug_info["category_details"][category_id] = category_debug
        
        if debug:
            # 유형 이름 매핑
            type_names = {}
            for type_obj in intermediate_types:
                type_names[type_obj.id] = type_obj.name
            
            print(f"\n=== 족보 계산 디버깅 ===")
            print(f"가중치: {weights}")
            
            for category_id, category_info in debug_info["category_details"].items():
                print(f"\n카테고리 {category_id}:")
                for keyword_info in category_info["keyword_scores"]:
                    print(f"  키워드: {keyword_info['keyword_name']} (순서: {keyword_info['selection_order']}, 가중치: {keyword_info['weight']})")
                    # 상위 3개 점수만 출력
                    sorted_scores = sorted(keyword_info["weighted_scores"].items(), key=lambda x: x[1], reverse=True)[:3]
                    for type_id, score in sorted_scores:
                        if score > 0:
                            print(f"    {type_names.get(type_id, type_id)}: {keyword_info['raw_scores'][type_id]} × {keyword_info['weight']} = {score}")
            
            print(f"\n최종 16개 유형 점수:")
            sorted_final = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            for type_id, score in sorted_final:
                if score > 0:
                    print(f"  {type_names.get(type_id, type_id)}: {score:.1f}")
        
        # 디버깅 정보를 결과에 포함
        if debug:
            return type_scores, debug_info
        
        return type_scores

    @classmethod
    def get_top_two_types_from_db(cls, type_scores: Dict[int, float], db: Session) -> Tuple[IntermediateType, IntermediateType]:
        """
        점수가 가장 높은 상위 2개 유형 반환
        
        Returns:
            (1순위 유형, 2순위 유형) - IntermediateType 객체
        """
        # 점수순으로 정렬
        sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 2개 ID 추출
        first_type_id = sorted_types[0][0] if sorted_types else 1
        second_type_id = sorted_types[1][0] if len(sorted_types) > 1 else 2
        
        # DB에서 유형 정보 조회
        first_type = db.query(IntermediateType).filter(IntermediateType.id == first_type_id).first()
        second_type = db.query(IntermediateType).filter(IntermediateType.id == second_type_id).first()
        
        return first_type, second_type

    @classmethod
    def get_final_type_from_db(cls, primary_type_id: int, secondary_type_id: int, db: Session) -> Optional[FinalType]:
        """
        DB에서 1순위, 2순위 유형 조합으로 최종 캐릭터 조회
        
        Returns:
            FinalType 객체 또는 None
        """
        # 정방향 조합 확인
        combination = db.query(TypeCombination).filter(
            and_(
                TypeCombination.primary_type_id == primary_type_id,
                TypeCombination.secondary_type_id == secondary_type_id
            )
        ).first()
        
        # 정방향이 없으면 역방향 확인
        if not combination:
            combination = db.query(TypeCombination).filter(
                and_(
                    TypeCombination.primary_type_id == secondary_type_id,
                    TypeCombination.secondary_type_id == primary_type_id
                )
            ).first()
        
        if combination:
            return db.query(FinalType).filter(FinalType.id == combination.final_type_id).first()
        
        # 기본값으로 1번 최종 유형 반환
        return db.query(FinalType).filter(FinalType.id == 1).first()

    @classmethod
    def validate_keyword_ids(cls, selected_keyword_ids: Dict[str, List[int]], db: Session) -> bool:
        """
        선택된 키워드 ID들이 DB에 존재하는지 검증
        """
        all_keyword_ids = []
        for keyword_ids in selected_keyword_ids.values():
            all_keyword_ids.extend(keyword_ids)
        
        # DB에서 존재하는 키워드 수 확인
        existing_count = db.query(SubKeyword).filter(SubKeyword.id.in_(all_keyword_ids)).count()
        
        return existing_count == len(all_keyword_ids)

    @classmethod
    def calculate_final_type(cls, selected_keyword_ids: Dict[str, List[int]], db: Session, debug: bool = False) -> Dict:
        """
        전체 유형 계산 프로세스 실행 (DB 기반)
        
        Args:
            selected_keyword_ids: {
                "1": [69, 70],      # category_id: [sub_keyword_ids]
                "2": [41],
                "3": [21, 19, 12]
            }
        
        Returns:
            {
                "primaryType": {
                    "id": 1,
                    "name": "스트레스 회복자",
                    "score": 12.3
                },
                "secondaryType": {
                    "id": 3,
                    "name": "피로 관리자", 
                    "score": 10.5
                },
                "finalType": {
                    "id": 1,
                    "name": "스트레스 조향사",
                    "animal": "고슴도치",
                    ...
                }
            }
        """
        # 1. 키워드 ID 유효성 검증
        if not cls.validate_keyword_ids(selected_keyword_ids, db):
            raise ValueError("Invalid keyword IDs provided")
        
        # 2. 16개 유형 점수 계산
        if debug:
            type_scores, debug_info = cls.calculate_type_scores_from_db(selected_keyword_ids, db, debug=True)
        else:
            type_scores = cls.calculate_type_scores_from_db(selected_keyword_ids, db, debug=False)
            debug_info = None
        
        # 3. 상위 2개 유형 선택
        primary_type, secondary_type = cls.get_top_two_types_from_db(type_scores, db)
        
        # 4. 최종 캐릭터 조회
        final_type = cls.get_final_type_from_db(primary_type.id, secondary_type.id, db)
        
        # 5. 응답 데이터 구성
        result = {
            "primaryType": {
                "id": primary_type.id,
                "name": primary_type.name,
                "score": round(type_scores[primary_type.id], 1),
                "description": primary_type.description,
                "characteristics": primary_type.characteristics
            },
            "secondaryType": {
                "id": secondary_type.id,
                "name": secondary_type.name,
                "score": round(type_scores[secondary_type.id], 1),
                "description": secondary_type.description,
                "characteristics": secondary_type.characteristics
            },
            "finalType": {
                "id": final_type.id,
                "name": final_type.name,
                "animal": final_type.animal,
                "group_name": final_type.group_name,
                "one_liner": final_type.one_liner,
                "overview": final_type.overview,
                "greeting": final_type.greeting,
                "hashtags": final_type.hashtags,
                "strengths": final_type.strengths,
                "weaknesses": final_type.weaknesses,
                "relationship_style": final_type.relationship_style,
                "behavior_pattern": final_type.behavior_pattern,
                "image_filename": final_type.image_filename,
                "image_filename_right": final_type.image_filename_right,
                "strength_icons": final_type.strength_icons,
                "weakness_icons": final_type.weakness_icons
            } if final_type else None,
            "calculation_details": {
                "selected_keyword_ids": selected_keyword_ids,
                "all_type_scores": {k: round(v, 1) for k, v in type_scores.items()}
            }
        }
        
        return result

    @classmethod
    def get_all_intermediate_types(cls, db: Session) -> List[IntermediateType]:
        """DB에서 모든 중간 유형 조회"""
        return db.query(IntermediateType).order_by(IntermediateType.display_order).all()

    @classmethod
    def get_final_type_by_id(cls, final_type_id: int, db: Session) -> Optional[FinalType]:
        """ID로 최종 유형 조회"""
        return db.query(FinalType).filter(FinalType.id == final_type_id).first()