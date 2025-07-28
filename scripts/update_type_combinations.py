"""
type_combinations 테이블을 32개 유형 조합식에 맞게 업데이트하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.models import TypeCombination
from type_mapping_data import get_all_combinations
from sqlalchemy.exc import IntegrityError

def update_type_combinations():
    """type_combinations 테이블을 새로운 매핑으로 업데이트"""
    db = next(get_db())
    
    try:
        # 기존 데이터 모두 삭제
        print("기존 type_combinations 데이터 삭제 중...")
        db.query(TypeCombination).delete()
        db.commit()
        
        # 새로운 조합 데이터 가져오기
        combinations = get_all_combinations()
        
        # 새로운 데이터 삽입
        print(f"새로운 조합 {len(combinations)}개 추가 중...")
        success_count = 0
        
        for primary_id, secondary_id, final_id in combinations:
            try:
                combination = TypeCombination(
                    primary_type_id=primary_id,
                    secondary_type_id=secondary_id,
                    final_type_id=final_id
                )
                db.add(combination)
                db.commit()
                success_count += 1
                print(f"✓ 추가됨: ({primary_id}, {secondary_id}) -> {final_id}")
            except IntegrityError as e:
                db.rollback()
                print(f"✗ 중복 또는 오류: ({primary_id}, {secondary_id}) -> {final_id}")
                print(f"  오류: {str(e)}")
        
        print(f"\n완료! 총 {success_count}/{len(combinations)}개 조합이 성공적으로 추가되었습니다.")
        
        # 통계 출력
        print("\n=== 최종 유형별 조합 수 ===")
        final_type_counts = {}
        for _, _, final_id in combinations:
            final_type_counts[final_id] = final_type_counts.get(final_id, 0) + 1
        
        for final_id in sorted(final_type_counts.keys()):
            print(f"최종 유형 {final_id}: {final_type_counts[final_id]}개 조합")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_type_combinations()