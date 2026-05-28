# Data Collection Guide: Korea Green Coffee Bean Imports (HS 090111)

> **Note (Day 3):** Collection is now automated via `scripts/fetch_imports.py`
> (Korea Customs Service OpenAPI). Run `python scripts/fetch_imports.py` to refresh.
> The manual KITA steps below are kept as a fallback / reference only.
> Schema note: the automated output adds a `country_code` column (ISO-2, e.g. BR).

## Target File

```
data/raw/korea_green_bean_imports_hs090111_2024_2026.csv
```

## Target Fields

```csv
year_month,hs_code,item_name,country,import_weight_kg,import_value_usd,source,notes
```

| Field | Description | Example |
|---|---|---|
| year_month | YYYY-MM format | 2024-01 |
| hs_code | Always 090111 | 090111 |
| item_name | Item description | Coffee, not roasted, not decaffeinated |
| country | Country of origin | Brazil |
| import_weight_kg | Import weight in kg | 12500000 |
| import_value_usd | Import value in USD | 45230000 |
| source | Data source name | KITA |
| notes | Any remarks | Preliminary data |

---

## Option 1: KITA 무역통계 (권장, 가장 편함)

**사이트:** 한국무역협회 무역통계 (stat.kita.net)

**단계:**
1. stat.kita.net 접속
2. 상단 메뉴 → 품목별 수출입 통계
3. HS 코드 입력: `090111`
4. 조회 기간: 2024년 1월 ~ 최신 월
5. 국가별 세분화 옵션 선택
6. 중량(kg) + 금액(USD) 항목 포함해서 조회
7. 엑셀 다운로드 → CSV로 변환 후 위 형식에 맞게 정리

**참고:**
- 당월 데이터는 확정치가 아닐 수 있음 (잠정치 표시 주의)
- 국가별로 나눠서 나오므로 행 단위로 입력

---

## Option 2: 관세청 수출입무역통계

**사이트:** 관세청 (unipass.customs.go.kr → 통계 메뉴)

**단계:**
1. unipass.customs.go.kr 접속
2. 수출입통계 → 품목별 통계
3. HS 코드 `090111` 입력
4. 기간 및 국가별 설정
5. 다운로드

---

## Option 3: KATI (농식품수출정보)

**사이트:** kati.net

**특징:** 농식품 특화 통계. 커피 수입 관련 분석 자료도 함께 있음.

---

## 데이터 입력 예시

수집한 데이터를 아래 형식으로 CSV에 입력:

```csv
year_month,hs_code,item_name,country,import_weight_kg,import_value_usd,source,notes
2024-01,090111,Coffee not roasted not decaffeinated,Brazil,8200000,28500000,KITA,
2024-01,090111,Coffee not roasted not decaffeinated,Vietnam,5100000,11200000,KITA,
2024-01,090111,Coffee not roasted not decaffeinated,Colombia,1800000,9300000,KITA,
2024-01,090111,Coffee not roasted not decaffeinated,Ethiopia,900000,4100000,KITA,
2024-01,090111,Coffee not roasted not decaffeinated,Others,2300000,7600000,KITA,aggregated
```

---

## 주의사항

- 중량 단위를 확인할 것 (ton → kg 변환 필요할 수 있음)
- 금액 단위를 확인할 것 (천 달러 단위로 표시되는 경우 ×1000 필요)
- 국가명은 영문으로 통일
- 국가별로 없고 합산만 있는 경우 country = "Total"로 기입
- 잠정치는 notes에 "Preliminary" 기재

---

## 완료 기준

- 2024-01 ~ 2026-04 (또는 최신 확정 월) 기간의 국가별 수입 데이터 입력
- 최소 Brazil, Vietnam, Colombia, Ethiopia + Others(기타) 포함
- source_tracker.csv 상태를 `collected`로 업데이트
