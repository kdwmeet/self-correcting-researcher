# Self-Correcting Research Agent (자가 수정 심층 리서치 에이전트)

## 1. 프로젝트 개요

이 프로젝트는 단발성 응답으로 끝나는 기존의 챗봇과 달리, 에이전트가 스스로 결과물의 품질을 평가하고 기준에 미달할 경우 외부 검색과 재작성을 반복하여 결과물의 수준을 끌어올리는 순환형(Cyclic) 자가 수정 아키텍처입니다.

LangGraph의 상태 순환 구조와 도구 호출(Tool Calling) 기능을 결합하여, 심층적인 조사가 필요한 비즈니스 리서치나 학술 주제에 대해 인간 편집장 수준의 엄격한 품질 관리를 자동화합니다.

## 2. 시스템 아키텍처 및 워크플로우

본 시스템은 3개의 핵심 노드가 꼬리를 물고 순환하는 구조로 설계되었습니다.

1. Research Node: DuckDuckGo 검색 엔진 도구를 호출하여 주제에 대한 최신 데이터를 수집합니다. 검토 노드에서 넘어온 피드백(보완점)이 있다면 해당 키워드를 중심으로 추가 검색을 수행합니다.
2. Draft Node: 수집된 누적 데이터를 바탕으로 심층 보고서 초안을 작성합니다.
3. Review Node (Self-Correction): 작성된 초안을 평가하여 논리가 빈약하거나 정보가 누락되었는지 확인합니다. 기준을 충족하면(is_acceptable=True) 파이프라인을 종료하고, 부족하다면 구체적인 피드백을 생성하여 다시 Research Node로 돌려보냅니다.
4. Infinite Loop Prevention: 무한 루프에 빠지는 것을 방지하기 위해 최대 수정 횟수(revision_count)를 3회로 제한하는 라우팅 방어 로직이 적용되어 있습니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5.4-nano (심도 있는 분석과 엄격한 검토를 위해 reasoning_effort="high" 적용)
* Orchestration: LangGraph (StateGraph 기반 순환형 라우팅 제어)
* Search Tool: DuckDuckGo Search (ddgs 패키지)
* Web Framework: Streamlit (순환 과정 로깅 및 최종 결과 렌더링)

## 4. 프로젝트 구조
```
self-correcting-researcher/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          
```
## 5. 핵심 준수 사항 (개발 가이드라인)

시스템의 안정성과 예외 처리를 위해 다음 규칙을 엄격히 준수합니다.

* 프롬프트 템플릿 보호: ChatPromptTemplate 구성 시 파이썬 f-string을 절대 사용하지 않습니다. 웹 검색 결과로 유입되는 예측 불가능한 텍스트 기호가 템플릿 파싱 에러를 일으키는 것을 막기 위해 .invoke() 단계에서 딕셔너리로 안전하게 치환합니다.
* 안전한 상태 참조: 상태 딕셔너리 접근 시 초기화 지연으로 인한 KeyError를 방지하기 위해 반드시 state.get("키", 기본값) 방식을 사용합니다.
* 스트리밍 예외 처리: 순환형 그래프 실행 시 반환되는 특정 노드의 state_update가 None일 수 있으므로, .items() 순회 시 if not state_update: continue 방어 로직을 필수로 적용합니다.
* 최신 패키지 의존성: 외부 검색 도구 사용 시 반드시 최신 패키지명(ddgs)을 requirements.txt에 명시합니다.

## 6. 설치 및 실행 가이드

### 6.1 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.
OPENAI_API_KEY=sk-your-api-key-here

### 6.2 의존성 설치 및 실행
uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py

## 7. 활용 예시

* 입력 주제: "양자 컴퓨팅 상용화가 금융 보안에 미치는 영향"
* 순환 과정 관찰:
  - 1회차: 기본적인 개념 및 전망 위주로 초안 작성.
  - 1차 검토: "구체적인 금융권 도입 사례와 해결책(QKD 등)에 대한 설명이 부족함"이라는 피드백과 함께 재작업 지시.
  - 2회차: 피드백을 바탕으로 양자 암호 통신(QKD) 및 금융사 사례를 추가 검색하여 보고서 보완.
  - 2차 검토: 논리적 깊이와 정보량이 기준을 통과하여 최종 보고서 승인 및 출력.

## 8. 실행 화면
<img width="1511" height="803" alt="스크린샷 2026-05-06 083020" src="https://github.com/user-attachments/assets/502d91b5-6c83-478b-bfa1-b6e8dada4e2e" />
