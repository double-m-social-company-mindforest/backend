#!/usr/bin/env python3
import os
from character_genealogy_data import CHARACTER_GENEALOGY

# 실제 DB 캐릭터 이름 목록
db_characters = list(CHARACTER_GENEALOGY.keys())

# 파일 시스템에서 캐릭터 이름 추출
icon_dir = "static/character_icons"
files = os.listdir(icon_dir)

# 파일에서 캐릭터 이름 추출 (숫자와 .svg 제거)
file_characters = set()
for file in files:
    if file.endswith('.svg'):
        # 숫자와 확장자 제거하여 캐릭터 이름만 추출
        char_name = file.replace('.svg', '')
        # 마지막 숫자 제거
        char_name = ''.join(char_name.split()[:-1]) if char_name.split()[-1].isdigit() else char_name.rstrip('123456')
        file_characters.add(char_name)

print("=== DB에 있는 32개 캐릭터 ===")
for i, char in enumerate(sorted(db_characters), 1):
    print(f"{i:2d}. {char}")

print(f"\n=== 아이콘 파일에서 발견된 캐릭터 ({len(file_characters)}개) ===")
for i, char in enumerate(sorted(file_characters), 1):
    print(f"{i:2d}. {char}")

# 누락된 캐릭터 찾기
missing_in_files = []
for db_char in db_characters:
    found = False
    for file_char in file_characters:
        if db_char.replace(' ', '_') == file_char or db_char == file_char.replace('_', ' '):
            found = True
            break
    if not found:
        missing_in_files.append(db_char)

# 추가된 캐릭터 찾기 (DB에 없지만 파일에 있는)
extra_in_files = []
for file_char in file_characters:
    found = False
    for db_char in db_characters:
        if db_char.replace(' ', '_') == file_char or db_char == file_char.replace('_', ' '):
            found = True
            break
    if not found:
        extra_in_files.append(file_char)

print(f"\n=== 누락된 캐릭터 ({len(missing_in_files)}개) ===")
for char in sorted(missing_in_files):
    print(f"- {char}")

print(f"\n=== DB에 없는 추가 캐릭터 ({len(extra_in_files)}개) ===")
for char in sorted(extra_in_files):
    print(f"- {char}")

# 각 캐릭터별 아이콘 개수 확인
print(f"\n=== 각 캐릭터별 아이콘 개수 확인 ===")
for db_char in sorted(db_characters):
    count = 0
    for file in files:
        if file.endswith('.svg'):
            file_base = file.replace('.svg', '').rstrip('123456')
            if db_char.replace(' ', '_') == file_base:
                count += 1
    
    if count != 6:
        print(f"⚠️  {db_char}: {count}개 (6개 필요)")
    else:
        print(f"✅ {db_char}: {count}개")