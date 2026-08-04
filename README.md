# Prompt Atelier

이미지 생성용 프롬프트를 10개 카테고리로 나눠 저장하고, 원하는 항목을 골라 하나의 프롬프트로 조합하는 로컬 웹 앱입니다.

## 구성

- **백엔드:** Python 표준 라이브러리 HTTP API (`backend/server.py`)
- **프런트엔드:** Node.js 정적 서버 및 API 프록시 (`frontend/server.js`) + JavaScript UI
- **프롬프트 저장:** `backend/storage/prompts.json`
- **사진 저장:** `backend/storage/images/`

SQLite나 별도 데이터베이스를 사용하지 않습니다. 사진은 JSON에 Base64로 넣지 않고 개별 파일로 보관하며, `prompts.json`에는 `/uploads/<UUID 파일명>` 형태의 매핑 경로만 기록합니다.

## Windows에서 가장 간단한 실행

1. 최초 한 번 `install.bat`을 더블클릭합니다.
   - Python 3.10 이상과 Node.js 18 이상의 설치 여부 및 버전을 확인합니다.
   - 없거나 버전이 낮으면 Windows `winget`으로 Python 3.12와 Node.js LTS를 설치합니다.
2. 설치 확인이 끝나면 `start.bat`을 더블클릭합니다.
   - Python 백엔드와 Node.js 프런트엔드를 함께 실행합니다.
   - 서버 준비 후 브라우저에서 웹사이트를 자동으로 엽니다.
3. 종료하려면 실행 창에서 `Ctrl+C`를 누릅니다.

> `winget`이 없는 Windows에서는 `install.bat`이 Microsoft의 **앱 설치 관리자** 설치 안내를 표시합니다.

## 터미널에서 실행

필요한 것은 **Python 3.10 이상**과 **Node.js 18 이상**뿐입니다. 외부 패키지 설치는 필요 없습니다.

```bash
npm start
```

두 서버가 함께 시작됩니다.

- 웹사이트: http://127.0.0.1:4173
- Python API: http://127.0.0.1:8000

종료할 때는 `Ctrl+C`를 누르세요.

각 서버를 따로 실행하려면 다음 명령을 사용합니다.

```bash
npm run start:backend
npm run start:frontend
```

## 저장 구조

프롬프트를 저장하면 Python 백엔드가 이미지 데이터의 형식과 크기를 확인하고 UUID 파일명으로 분리해 저장합니다.

```text
backend/storage/
├── prompts.json
└── images/
    ├── 0ea64f086ab04d53a8499d86fe64bd33.jpg
    └── b4acaaeb71d8464489f22bdf0c697151.webp
```

`prompts.json` 예시:

```json
[
  {
    "id": "e4b233ca-7915-4f55-b2d4-3e1e5da90413",
    "category": "face",
    "title": "내추럴 글로우",
    "prompt": "natural dewy skin, subtle peach blush",
    "images": [
      "/uploads/0ea64f086ab04d53a8499d86fe64bd33.jpg"
    ]
  }
]
```

프롬프트를 삭제하면 더 이상 참조하지 않는 사진 파일도 같이 삭제됩니다. 전체 데이터를 백업하려면 `backend/storage/` 폴더를 복사하면 됩니다.

## 테스트

```bash
npm test
```
