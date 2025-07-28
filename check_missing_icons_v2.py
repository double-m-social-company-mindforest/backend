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

# 파일에서 캐릭터 이름 추출
file_characters = {}
for file in svg_files:
    # 파일명에서 숫자와 .svg 제거
    base_name = re.sub(r'[0-9]+\.svg$', '', file)
    
    if base_name not in file_characters:
        file_characters[base_name] = 0
    file_characters[base_name] += 1

print("=== 파일 시스템의 캐릭터별 아이콘 개수 ===")
for char, count in sorted(file_characters.items()):
    print(f"{char}: {count}개")

print(f"\n파일 시스템에서 발견된 캐릭터 수: {len(file_characters)}")

# DB 캐릭터 이름을 파일명 형식으로 변환
db_to_file_mapping = {}
for db_char in db_characters:
    # 공백을 언더스코어로 변경
    file_format = db_char.replace(' ', '_')
    db_to_file_mapping[db_char] = file_format

print(f"\n=== DB 캐릭터와 파일명 매핑 ===")
for db_char, file_format in sorted(db_to_file_mapping.items()):
    count = file_characters.get(file_format, 0)
    status = "✅" if count == 6 else "⚠️" 
    print(f"{status} {db_char} → {file_format}: {count}개")

# 누락된 캐릭터 목록
missing_characters = []
for db_char, file_format in db_to_file_mapping.items():
    if file_format not in file_characters:
        missing_characters.append(db_char)

print(f"\n=== 완전히 누락된 캐릭터 ({len(missing_characters)}개) ===")
for char in sorted(missing_characters):
    print(f"- {char}")

# 아이콘이 부족한 캐릭터 목록
incomplete_characters = []
for db_char, file_format in db_to_file_mapping.items():
    count = file_characters.get(file_format, 0)
    if 0 < count < 6:
        incomplete_characters.append((db_char, count))

print(f"\n=== 아이콘이 부족한 캐릭터 ({len(incomplete_characters)}개) ===")
for char, count in sorted(incomplete_characters):
    print(f"- {char}: {count}개 (6개 필요)")

# 파일 시스템에 있지만 DB에 없는 캐릭터
extra_characters = []
for file_char in file_characters.keys():
    if file_char not in db_to_file_mapping.values():
        extra_characters.append(file_char)

print(f"\n=== DB에 없는 추가 캐릭터 ({len(extra_characters)}개) ===")
for char in sorted(extra_characters):
    print(f"- {char}: {file_characters[char]}개")