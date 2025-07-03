# Link Music API Documentation

## 🧭 Overview

Link Music API는 사용자로부터 입력받은 **텍스트 또는 이미지**를 기반으로, 인공지능 분석을 통해 **분위기(Mood)** 를 추출하고, 이를 바탕으로 요청 내용에 어울리는 비신탁 음원을 추천합니다. 콘텐츠 플랫폼, 공공기관, 창작자들이 빠르고 적절한 배경음악을 자동 추천받을 수 있도록 설계된 서비스입니다.

## 🔐 Authentication

모든 API 요청은 다음 필드를 HTTP 헤더에 포함해야 합니다:

```json
Authorization: Bearer ${YOUR_API_KEY}
```

> API 키는 별도 발급이 필요합니다.
> 

## 🧠 Analyze Input - Text

### `POST` `/v2/analyze/text`

텍스트를 분석하여 분위기 키워드를 추출하기 위한 요청을 생성합니다.

### 📥 Request Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `text_input` | string | Yes | 사용자 텍스트 입력 (한글 기준 최대 1,000자) |
| `take` | integer | No | 추천받을 음원 수량 (1–10, 기본값 1) |

> 본 API는 결과를 직접 반환하지 않으며, 분석 처리를 위한 중간 단계입니다
> 

### 📤 Response

```bash
curl -X 'POST' \
  'https://api-prod.linkmusic.io/v2/analyze/text' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer ${YOUR_API_KEY}' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'message=%EC%8B%A0%EB%82%98%EA%B3%A0%20%EA%B2%BD%EC%BE%8C%ED%95%9C%20%EB%B9%84%ED%8A%B8%EC%9D%98%20%EC%9D%8C%EC%95%85%EC%9D%84%20%EC%B6%94%EC%B2%9C%ED%95%B4%EC%A4%98&take=N'
```

```json
{
  "musics": [
    {
      "id": "MUSIC_ID",
      "duration": 146,
      "source": "MUSIC_SOURCE_LOCATION",
      "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
      "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
      "deleted_at": null,
      "genre": {
        "id": "GENRE_ID",
        "name": "GENRE_NAME",
        "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
        "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
        "deleted_at": null
      },
      "moods": [
        {
          "music_id": "MUSIC_ID",
          "mood_id": "MOOD_ID",
          "detail": {
            "name": "MOOD_NAME",
            "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
            "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
            "deleted_at": null
          }
        }
      ]
    }
  ],
  "cursor": {
    "id": "MUSIC_ID",
    "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ"
  } || null
}
```

## 🧠 Analyze Input - Image

### `POST` `/v2/analyze/image`

이미지를 분석하여 분위기 키워드를 추출하기 위한 요청을 생성합니다.

### 📥 Request Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `image_input` | file | Yes | 이미지 파일 업로드 (`jpeg`, `png`, `gif`, `jpg`, `webp`, `bmp`)최대 3MB) |
| `take` | integer | No | 추천받을 음원 수량 (1–10, 기본값 1) |

> 본 API는 결과를 직접 반환하지 않으며, 분석 처리를 위한 중간 단계입니다.
> 

### 📤 Response

```bash
curl -X 'POST' \
  'https://api-prod.linkmusic.io/v2/analyze/images' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer ${YOUR_API_KEY}' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@파일명;type=image/확장자' \
  -F 'take=N'
```

```json
{
  "musics": [
    {
      "id": "MUSIC_ID",
      "duration": 146,
      "source": "MUSIC_SOURCE_LOCATION",
      "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
      "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
      "deleted_at": null,
      "genre": {
        "id": "GENRE_ID",
        "name": "GENRE_NAME",
        "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
        "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
        "deleted_at": null
      },
      "moods": [
        {
          "music_id": "MUSIC_ID",
          "mood_id": "MOOD_ID",
          "detail": {
            "name": "MOOD_NAME",
            "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
            "updated_at": "YYYY-MM-DDTHH:MM:SS.SSSZ",
            "deleted_at": null
          }
        }
      ]
    }
  ],
  "cursor": {
    "id": "MUSIC_ID",
    "created_at": "YYYY-MM-DDTHH:MM:SS.SSSZ"
  } || null
}
```

### ⛔ Error Cases

| 에러 상황 | 코드 | 메시지 예시 | 설명 |
| --- | --- | --- | --- |
| `text_input` 과 `image_input`모두 없는 경우 | `400 Bad Request` | 텍스트 또는 이미지 입력 중 하나는 필수입니다. | 최소 입력값 누락 |
| 미 지원 이미지 파일 확장자 업로드 | `415 Unsupported Media Type` | 지원하지 않는 파일 형식입니다. 지원 형식(`jpeg, png, gif, jpg, webp, bmp`) | 이미지 파일 형식 오류 |
| 용량이 너무 큰 이미지 업로드 (”img”>3MB) | `400 Bad Request` | 이미지 용량은 3MB를 초과할 수 없습니다. | 이미지 업로드 용량 제한 초과(3MB 이상 업로드 불가) |
| 텍스트 길이 제한 초과(한글 N자) | `400 Bad Request` | 텍스트 입력은 최대 N자 입니다. (사용자 기준) | 텍스트 입력 최대 길이 초과 |
| 텍스트 길이 제한 미달(최소 1자 미만or공백 입력 Only) | `400 Bad Request` | 텍스트 입력이 감지 되지않았습니다. | 텍스트 입력 없음 |
| 음원 요청 수량 제한 초과 (n>100) | `400 Bad Request` | 요청 수량은 1~10 사이여야 합니다. | 1회 요청량 제한 초과 (10개/회) |
| API 키 유효성 문제 | `401 Unauthorized` |  |  |

---

## 🎵 Music Recommendation (Cursor)

### `GET` `v2/pagination/cursor`

추천된 음원을 기반으로 음원 DB에서 최대 10개의 음원을 Cursor 기반 Pagination을 제공합니다.

상기 Text, Image 분석을 선행 해야 쿼리가 가능합니다

### 📥 Request Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `take` | integer | No | 요청 음원 개수 (1~10, 기본값 1) |
| `id` | array[string] | Yes | Cursor의 Primary Key |
| `created_at`  | array[string] | Yes | The creation date of the cursor |

### 📤 Response