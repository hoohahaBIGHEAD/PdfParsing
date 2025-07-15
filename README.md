# PDF to Markdown/Text 변환 도구

세 가지 고성능 PDF 파싱 도구(`Marker`, `Docling`, `LlamaParse`)를 비교하고 배치 처리 스크립트를 제공합니다.

## ⚡ 빠른 실행

```bash
# 1. 환경 설정
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. PDF 파일을 pdf_source/ 폴더에 복사

# 3. 원하는 도구로 실행
python run_marker_batch.py    # 🏠 로컬, 고품질, 이미지 추출
python run_docling_batch.py   # 🌐 다중 포맷, 생태계 통합  
python run_llama_batch.py     # ⚡ AI 파싱, API 키 필요
```

## 📊 도구 선택 가이드

| 상황 | 추천 도구 | 이유 |
|------|----------|------|
| 🔒 민감한 데이터 | **Marker** | 완전 로컬 실행 |
| 🎯 최고 품질 | **LlamaParse** | GPT-4o 비전 모델 |
| 🔗 다양한 포맷 | **Docling** | PDF/DOCX/PPTX 지원 |
| 💰 무료 솔루션 | **Marker/Docling** | API 키 불필요 |

## 📁 프로젝트 구조

```
PdfParsing/
├── pdf_source/                    # 원본 PDF 파일 위치
├── conversion_results/            # 변환 결과 저장소
│   ├── marker/                   # Marker 결과
│   ├── docling/                  # Docling 결과
│   └── llama_cloud/              # LlamaParse 결과
├── run_marker_batch.py           # Marker 배치 처리 스크립트
├── run_docling_batch.py          # Docling 배치 처리 스크립트
├── run_llama_batch.py            # LlamaParse 배치 처리 스크립트
├── requirements.txt              # Python 의존성 목록
├── .gitignore                    # Git 버전 관리 제외 파일
├── .venv/                        # uv 가상환경 (생성 후)
└── .env                          # 환경변수 (LlamaParse API 키)
```

---

## 📋 상세 설정 가이드

### 1. uv 설치 (없는 경우)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 가상환경 설정 및 의존성 설치
```bash
# 가상환경 생성
uv venv .venv

# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 의존성 설치
uv pip install -r requirements.txt
```

### 3. PDF 파일 준비
```bash
# pdf_source/ 폴더에 PDF 파일들을 위치시킵니다
mkdir -p pdf_source
cp your_pdfs.pdf pdf_source/
```

### 4. LlamaParse API 키 설정 (선택사항)
```bash
# .env 파일 생성
echo "LLAMA_CLOUD_API_KEY=llx-your-api-key-here" > .env
```

### 5. 실행
```bash
# Marker: 로컬 고품질 변환
python run_marker_batch.py

# Docling: 다중 포맷 지원  
python run_docling_batch.py

# LlamaParse: AI 기반 파싱 (API 키 필요)
python run_llama_batch.py
```

---

## 📖 도구별 상세 정보

### 1. Marker - 로컬 고품질 변환
> [GitHub: VikParuchuri/marker](https://github.com/VikParuchuri/marker)

**특징**: 완전 로컬 실행, 고품질 마크다운 변환, 풍부한 메타데이터
- 🏠 로컬 실행으로 데이터 보안 확보
- 🖼️ 이미지 자동 추출 및 저장 (PDF당 4-5개)
- 📊 1500+줄의 상세 메타데이터 (목차, 페이지 정보, 좌표 등)
- ⚡ GPU 가속 (CUDA, Apple Silicon MPS)

**실행**: `python run_marker_batch.py`  
**결과**: 마크다운 + 1500+줄 메타데이터 + 이미지 파일들

### 2. Docling - 다중 포맷 지원
> [GitHub: DS4SD/docling](https://github.com/DS4SD/docling)

**특징**: 다양한 문서 포맷 지원, GenAI 생태계 통합, 이미지 링크 자동 처리
- 📄 다중 포맷 지원 (PDF, DOCX, PPTX, XLSX, HTML)
- 🔗 LangChain, LlamaIndex, Haystack 등과 통합
- 🖼️ 마크다운 이미지 링크 자동 생성 및 URL 인코딩
- 🏠 로컬 실행 및 에어갭 환경 지원

**실행**: `python run_docling_batch.py`  
**결과**: URL 인코딩된 이미지 링크가 포함된 마크다운 + _artifacts/ 이미지 폴더

### 3. LlamaParse - AI 기반 클라우드 파싱
> [Docs: LlamaParse](https://docs.cloud.llamaindex.ai/llamaparse/getting_started)

**특징**: GPT-4o 비전 모델 활용, 클라우드 기반, 마크다운+텍스트 동시 출력
- 🤖 GPT-4o 비전 모델로 고품질 AI 파싱
- 📊 복잡한 표, 차트, 다단 레이아웃 처리에 특화
- 🔄 마크다운과 텍스트 동시 생성
- ⚡ 비동기 병렬 처리 (4개 워커)
- 🎯 RAG 최적화 및 LlamaIndex 생태계 통합
- 💰 **API 키 필요** ([LlamaCloud](https://cloud.llamaindex.ai/api-key)에서 발급)

**실행**: `python run_llama_batch.py` (API 키가 .env 파일에 있어야 함)  
**결과**: 구조화된 마크다운 + 깔끔한 순수 텍스트 (동시 생성)



---

## 📊 상세 비교 및 성능

| 특징 | Marker | Docling | LlamaParse |
|------|--------|---------|------------|
| **실행 환경** | 🏠 로컬 | 🏠 로컬 | ☁️ 클라우드 |
| **속도** | 19.2초/파일 | 28.5초/파일 | 10.9초/파일 |
| **품질** | 🥇 우수 | 🥈 좋음 | 🥇 우수 |
| **이미지 처리** | ✅ 추출+저장 | ✅ 추출+링크 | ✅ 감지 |
| **메타데이터** | ✅ 매우 풍부 (1500+줄) | ✅ 기본 | ❌ 없음 |
| **출력 형식** | 📝 Markdown | 📝 Markdown | 📝📄 MD + Text |
| **API 키** | ❌ | ❌ | ✅ 필요 |
| **비용** | 🆓 무료 | 🆓 무료 | 💰 유료 |
| **GPU 지원** | ✅ CUDA, MPS | ✅ CUDA, MPS | ❌ |
| **병렬 처리** | ✅ 멀티프로세싱 | ✅ 멀티프로세싱 | ✅ 비동기 |

---

## 🔧 추가 설정

### GPU 메모리 최적화
GPU 메모리가 부족한 경우 각 스크립트 상단에서 워커 수를 줄일 수 있습니다:
```python
MAX_WORKERS_CUDA = 1  # 기본값 2에서 1로 감소
```

### LlamaParse API 키
[LlamaCloud](https://cloud.llamaindex.ai/api-key)에서 API 키 발급 후 `.env` 파일에 저장:
```bash
LLAMA_CLOUD_API_KEY=llx-your-api-key-here
```

---

## 📝 라이선스

- **Marker**: Apache 2.0
- **Docling**: MIT  
- **LlamaParse**: 상업적 서비스 