-- 32개 유형별 조합식에 따른 type_combinations 데이터 삽입
-- 1. 스트레스 조향사
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(1, 3, 1), (1, 4, 1), (1, 5, 1), (1, 7, 1), (1, 8, 1), (1, 14, 1), (1, 15, 1);

-- 2. 불안 정복자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(2, 1, 2), (2, 4, 2), (2, 7, 2), (2, 8, 2), (2, 14, 2), (2, 16, 2);

-- 3. 피로 관리자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(3, 1, 3), (3, 9, 3), (3, 10, 3), (3, 11, 3), (3, 12, 3), (3, 13, 3), (3, 16, 3);

-- 4. 감정 연금술사
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(4, 1, 4), (4, 2, 4), (4, 3, 4), (4, 5, 4), (4, 6, 4), (4, 7, 4), (4, 8, 4),
(4, 10, 4), (4, 12, 4), (4, 13, 4), (4, 14, 4), (4, 15, 4), (4, 16, 4);

-- 5. 소통 해소자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(1, 9, 5), (1, 10, 5), (1, 11, 5), (1, 12, 5), (2, 9, 5), (2, 10, 5), (2, 11, 5), (2, 12, 5);

-- 6. 긍정 전환자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(1, 13, 6), (2, 13, 6), (2, 15, 6);

-- 7. 효율 불안 해결사
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(2, 5, 7), (2, 6, 7), (3, 2, 7), (3, 7, 7), (7, 2, 7);

-- 8. 안정 피로전사
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(3, 4, 8), (3, 5, 8), (3, 6, 8), (3, 14, 8), (3, 15, 8);

-- 9. 목표 달성자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(5, 1, 9), (5, 2, 9), (5, 3, 9), (5, 4, 9), (5, 7, 9), (5, 8, 9);

-- 10. 성장 추구자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(6, 1, 10), (6, 2, 10), (6, 3, 10), (6, 4, 10), (6, 5, 10), (6, 8, 10), (6, 14, 10);

-- 11. 시간 관리 마스터
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(7, 1, 11), (7, 3, 11), (7, 4, 11), (7, 5, 11), (7, 6, 11), (7, 8, 11);

-- 12. 자신감 승리자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(8, 1, 12), (8, 2, 12), (8, 3, 12), (8, 4, 12), (8, 5, 12), (8, 6, 12), (8, 7, 12);

-- 13. 활동 성장가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(5, 9, 13), (5, 10, 13), (5, 11, 13), (5, 16, 13), (6, 9, 13), (6, 10, 13), (6, 16, 13);

-- 14. 안정 효율 주의자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(7, 9, 14), (7, 10, 14), (7, 11, 14), (7, 12, 14), (7, 14, 14), (7, 15, 14), (7, 16, 14);

-- 15. 자신감 개척자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(8, 9, 15), (8, 10, 15), (8, 11, 15), (8, 12, 15), (8, 14, 15), (8, 15, 15), (8, 16, 15);

-- 16. 긍정 탐구자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(5, 13, 16), (6, 13, 16), (7, 13, 16), (8, 13, 16);

-- 17. 관계 복원가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(9, 1, 17), (9, 2, 17), (9, 3, 17), (9, 4, 17), (9, 5, 17), (9, 6, 17), (9, 7, 17), (9, 8, 17);

-- 18. 팀워크 장인
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(10, 1, 18), (10, 2, 18), (10, 3, 18), (10, 4, 18), (10, 5, 18), (10, 6, 18), (10, 7, 18), (10, 8, 18);

-- 19. 소통 달인
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(11, 1, 19), (11, 2, 19), (11, 3, 19), (11, 4, 19), (11, 5, 19), (11, 6, 19), (11, 7, 19), (11, 8, 19);

-- 20. 감정 공유자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(12, 1, 20), (12, 2, 20), (12, 3, 20), (12, 4, 20), (12, 5, 20), (12, 6, 20), (12, 7, 20), (12, 8, 20);

-- 21. 마음 나눔가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(4, 9, 21), (9, 10, 21), (9, 11, 21), (9, 12, 21), (10, 9, 21), (11, 9, 21), (12, 9, 21);

-- 22. 긍정 대화가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(4, 11, 22), (10, 11, 22), (11, 10, 22), (11, 12, 22), (11, 13, 22), (11, 14, 22), (11, 15, 22), (11, 16, 22);

-- 23. 모험 낙관주의자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(13, 1, 23), (13, 2, 23), (13, 3, 23), (13, 4, 23), (13, 9, 23), (13, 10, 23), (13, 11, 23), (13, 12, 23);

-- 24. 안정 낙관주의자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(15, 1, 24), (15, 2, 24), (15, 3, 24), (15, 4, 24), (15, 9, 24), (15, 10, 24), (15, 11, 24), (15, 12, 24);

-- 25. 긍정 목표쟁취자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(5, 15, 25), (6, 15, 25), (13, 5, 25), (13, 6, 25), (13, 7, 25), (13, 8, 25), (15, 5, 25), (15, 6, 25);

-- 26. 따뜻한 낙관가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(9, 13, 26), (9, 14, 26), (9, 15, 26), (10, 13, 26), (10, 14, 26), (10, 15, 26), (12, 10, 26), (12, 11, 26);

-- 27. 자유 크리에이터
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(14, 1, 27), (14, 2, 27), (14, 3, 27), (14, 4, 27), (14, 5, 27), (14, 6, 27), (14, 7, 27), (14, 8, 27);

-- 28. 창의 성장자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(14, 9, 28), (14, 10, 28), (14, 11, 28), (14, 12, 28), (14, 13, 28), (14, 15, 28), (14, 16, 28);

-- 29. 몰입 활동가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(16, 1, 29), (16, 2, 29), (16, 3, 29), (16, 4, 29), (16, 5, 29), (16, 6, 29), (16, 7, 29),
(16, 8, 29), (16, 9, 29), (16, 10, 29), (16, 11, 29), (16, 12, 29), (16, 13, 29), (16, 14, 29), (16, 15, 29);

-- 30. 활동 해소자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(1, 6, 30), (1, 16, 30), (2, 3, 30), (5, 14, 30), (6, 12, 30), (12, 13, 30), (12, 14, 30), (13, 14, 30);

-- 31. 성장 극복자
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(1, 2, 31), (3, 8, 31), (5, 6, 31), (5, 12, 31), (6, 7, 31), (6, 11, 31), (10, 16, 31);

-- 32. 활동 소통가
INSERT INTO type_combinations (primary_type_id, secondary_type_id, final_type_id) VALUES
(9, 16, 32), (10, 12, 32), (12, 15, 32), (12, 16, 32), (13, 15, 32), (13, 16, 32),
(15, 7, 32), (15, 8, 32), (15, 13, 32), (15, 14, 32), (15, 16, 32);