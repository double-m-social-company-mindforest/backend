#!/usr/bin/env python3
import os
import re
from character_genealogy_data import CHARACTER_GENEALOGY

# 실제 DB 캐릭터 이름 목록
db_characters = list(CHARACTER_GENEALOGY.keys())

# 파일 시스템에서 파일 목록 가져오기
icon_dir = "static/character_icons"
files = os.listdir(icon_dir)
svg_files = [f for f in files if f.endswith('.svg')]

print(f"총 SVG 파일 수: {len(svg_files)}")
print(f"예상 파일 수: {32 * 6} = 192개")
print()

# 파일에서 캐릭터 이름 추출 (더 정확한 방법)
file_characters = {}
for file in svg_files:
    # 파일명에서 마지막 숫자와 .svg 제거
    base_name = re.sub(r'\d+\.svg$', '', file)
    
    if base_name not in file_characters:
        file_characters[base_name] = []
    
    # 파일 번호 추출
    match = re.search(r'(\d+)\.svg$', file)
    if match:
        file_number = int(match.group(1))
        file_characters[base_name].append(file_number)

print(f"파일 시스템에서 발견된 캐릭터 수: {len(file_characters)}")

# 각 캐릭터별 아이콘 개수와 번호 확인
print("\n=== 각 캐릭터별 아이콘 상세 정보 ===")
total_files = 0
for char in sorted(file_characters.keys()):
    numbers = sorted(file_characters[char])
    count = len(numbers)
    total_files += count
    
    status = "✅" if count == 6 and numbers == [1, 2, 3, 4, 5, 6] else "⚠️"
    missing_numbers = [i for i in range(1, 7) if i not in numbers]
    
    print(f"{status} {char}: {count}개 {numbers}")
    if missing_numbers:
        print(f"    누락된 번호: {missing_numbers}")
    if count > 6:
        print(f"    초과된 파일들: {[n for n in numbers if n > 6]}")

print(f"\n총 계산된 파일 수: {total_files}")

# DB 캐릭터와 매칭
print(f"\n=== DB 캐릭터 매칭 결과 ===")
db_to_file_exact = {}

for db_char in db_characters:
    # 여러 가능한 파일명 형식 시도
    possible_names = [
        db_char.replace(' ', '_'),  # 공백을 언더스코어로
        db_char.replace(' ', ''),   # 공백 제거
        db_char  # 원본 그대로
    ]
    
    matched = False
    for possible_name in possible_names:
        if possible_name in file_characters:
            db_to_file_exact[db_char] = possible_name
            matched = True
            break
    
    if not matched:
        db_to_file_exact[db_char] = None

# 매칭 결과 출력
matched_count = 0
for db_char in sorted(db_characters):
    file_name = db_to_file_exact[db_char]
    if file_name:
        count = len(file_characters[file_name])
        status = "✅" if count == 6 else "⚠️"
        print(f"{status} {db_char} → {file_name}: {count}개")
        matched_count += 1
    else:
        print(f"❌ {db_char}: 매칭 실패")

print(f"\n매칭된 DB 캐릭터: {matched_count}/{len(db_characters)}")

# 매칭되지 않은 파일들
unmatched_files = []
matched_file_names = set(db_to_file_exact.values())
matched_file_names.discard(None)

for file_char in file_characters.keys():
    if file_char not in matched_file_names:
        unmatched_files.append(file_char)

if unmatched_files:
    print(f"\n=== 매칭되지 않은 파일 캐릭터 ({len(unmatched_files)}개) ===")
    for char in sorted(unmatched_files):
        print(f"- {char}: {len(file_characters[char])}개")