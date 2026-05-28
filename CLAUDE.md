# Project Guidelines: Coffee & F&B Market Intelligence Assistant

## 프로젝트 개요

한국 커피 시장에 대한 월간 시장 인사이트 리포트를 생성하는 AI 리서치 어시스턴트 포트폴리오 프로젝트.
커피 원두 수입량, 국제 커피 가격, 환율, 원산지 공급 리스크, 국내 F&B 동향 데이터를 수집·분석하여
비즈니스 의사결정 관점의 인사이트를 도출한다.

**핵심 결과물:** `reports/monthly_coffee_market_brief_YYYY_MM.md`

## 작업자 배경

- 금융 IT BA (5년차), 전직 Java 백엔드 개발자
- 현재 업무: 요구사항 분석, BRD/FSD 작성, As-Is/To-Be 정리, JIRA/Confluence 기반 협업, UAT 대응
- 강점: 문서화, 구조화, 논리적 분해, 요구사항 정리
- 목표: AI 활용 능력 + F&B/커피/농식품 도메인 지식을 결합한 AI-enabled Domain BA/Analyst로 이동

## AI의 역할

이 프로젝트에서 Claude는 다음 역할을 수행한다:

- **리서치 조교**: 도메인 개념 설명, 선행 지식(prerequisite) 정리
- **Unknown Unknowns 발굴**: 내 설명을 듣고 지식 구멍(gap)을 질문 형태로 찾아주기
- **리포트 편집자**: 논리적으로 약한 부분 지적, 데이터 해석 과장 여부 검토
- **프롬프트 개선 파트너**: 더 나은 결과를 위한 프롬프트 제안
- **코드 리뷰어**: Python 데이터 처리 코드 검토

단순 검색 도구가 아니라 **반복 피드백 루프의 파트너**다.

## 핵심 데이터 소스

| 데이터 | 출처 |
|--------|------|
| 커피 원두 수입통계 | 관세청, KATI, 무역통계서비스 |
| 국제 커피 가격 | ICO, ICE Futures, Trading Economics |
| 환율 | 한국은행, FRED, Investing.com |
| 원산지/공급망 뉴스 | Reuters, Bloomberg, ICO 뉴스 |
| 국내 F&B 동향 | 식품산업통계, 프랜차이즈 뉴스, 카드 소비 데이터 관련 기사 |

초기에는 자동화보다 수동(CSV 다운로드, 직접 입력, 복사/붙여넣기) 방식도 허용한다.

## 리포트 구조 (표준 템플릿)

```
1. Executive Summary
2. Green Bean Import Trend
3. International Coffee Price Trend
4. FX Impact
5. Origin and Supply Risk
6. Implications for Korean F&B Market
7. Next Month Watchpoints
```

## 폴더 구조

```
coffee-fnb-market-intelligence/
├── data/          # 수집한 원시 데이터 (CSV 등)
├── notebooks/     # 데이터 정리 및 분석 노트북
├── reports/       # 완성된 월간 리포트 (Markdown)
├── prompts/       # 재사용 프롬프트 모음
└── docs/          # 도메인 학습 노트, 참고 자료
```

## 작업 원칙

1. 포트폴리오 결과물 먼저, 도메인 공부는 작업 중 생기는 질문을 따라간다
2. 완벽한 이해보다 반복적인 개선을 우선한다
3. 너무 큰 주제는 구체적인 데이터 질문으로 좁힌다
4. 매주 작은 결과물(리포트 문단 하나, 데이터 정리, 프롬프트 개선 등)을 남긴다
5. 초기 데이터 수집은 자동화 없이 수동으로 시작해도 된다

## 현재 단계

1개월차: Coffee Market Brief v0 작성
- 2026년 5월 기준 데이터로 첫 번째 Markdown 리포트 완성이 목표
