# 🔍 계층적 필터링 시스템 사용 가이드

## 📋 개요
인플루언서 모니터링 대시보드에서 **브랜드 → 월 → 캠페인** 순서로 단계별 필터링이 가능한 새로운 API 시스템입니다.

## 🎯 새로운 API 엔드포인트

### 1. 📊 **전체 계층적 필터 옵션 조회**
```http
GET /api/influencer-monitoring/filter-options/hierarchical
```

**응답 예시:**
```json
{
  "hierarchical_filters": [
    {
      "brand_id": "M",
      "brand_name": "MLB",
      "total_campaigns": 45,
      "months": [
        {
          "month_key": "2025-07",
          "month_display": "2025년 07월",
          "campaign_count": 12,
          "campaigns": [
            {
              "campaign_id": "camp_001",
              "camp_code": "MLB_2507_01",
              "camp_nm": "25FW MLB 신상 캠페인",
              "status": "CASTING"
            },
            {
              "campaign_id": "camp_002", 
              "camp_code": "MLB_2507_02",
              "camp_nm": "MLB 여름 컬렉션",
              "status": "DELIVERING"
            }
          ]
        },
        {
          "month_key": "2025-06",
          "month_display": "2025년 06월",
          "campaign_count": 8,
          "campaigns": [...]
        }
      ]
    },
    {
      "brand_id": "D",
      "brand_name": "디스커버리 익스페디션",
      "total_campaigns": 32,
      "months": [...]
    }
  ],
  "summary": {
    "total_brands": 4,
    "total_campaigns": 123
  }
}
```

### 2. 🏢 **브랜드 목록 조회**
```http
GET /api/influencer-monitoring/filter-options/brands
```

**응답 예시:**
```json
{
  "brands": [
    {
      "brand_id": "M",
      "brand_name": "MLB",
      "campaign_count": 45
    },
    {
      "brand_id": "D", 
      "brand_name": "디스커버리 익스페디션",
      "campaign_count": 32
    }
  ],
  "total": 4
}
```

### 3. 📅 **브랜드별 월 목록 조회**
```http
GET /api/influencer-monitoring/filter-options/brands/M/months
```

**응답 예시:**
```json
{
  "brand_id": "M",
  "months": [
    {
      "month_key": "2025-07",
      "month_display": "2025년 07월",
      "campaign_count": 12
    },
    {
      "month_key": "2025-06", 
      "month_display": "2025년 06월",
      "campaign_count": 8
    }
  ],
  "total": 6
}
```

### 4. 📋 **브랜드+월별 캠페인 목록**
```http
GET /api/influencer-monitoring/filter-options/brands/M/months/2025-07/campaigns
```

**응답 예시:**
```json
{
  "brand_id": "M",
  "month": "2025-07",
  "campaigns": [
    {
      "campaign_id": "camp_001",
      "camp_code": "MLB_2507_01", 
      "camp_nm": "25FW MLB 신상 캠페인",
      "status": "CASTING",
      "start_date": "2025-07-01",
      "end_date": "2025-07-31",
      "target_cnt": 50,
      "actual_influencer_count": 28
    }
  ],
  "total": 12
}
```

## 🎛️ 다중 필터 적용된 캠페인 조회

### 1. **브랜드별 필터링**
```http
GET /api/influencer-monitoring/campaigns?brand_id=M&limit=20
```

### 2. **브랜드 + 월별 필터링**
```http
GET /api/influencer-monitoring/campaigns?brand_id=M&month=2025-07&limit=20
```

### 3. **특정 캠페인들만 선택**
```http
GET /api/influencer-monitoring/campaigns?campaign_ids=camp_001,camp_002,camp_003
```

### 4. **전체 조합 필터링**
```http
GET /api/influencer-monitoring/campaigns?brand_id=M&month=2025-07&status=CASTING&campaign_ids=camp_001,camp_002
```

**응답 구조:**
```json
{
  "campaigns": [
    {
      "campaign_id": "camp_001",
      "camp_nm": "25FW MLB 신상 캠페인",
      "status": "CASTING",
      "progress_summary": {
        "AWAITING_RESPONSE": 15,
        "ACCEPTED": 8,
        "AWAITING_SHIPPING": 3,
        "COMPLETE": 2
      },
      "total_influencers": 28,
      "completion_rate": 7.14,
      "content_upload_rate": 25.0,
      "delivery_completion_rate": 85.7,
      "upcoming_deadlines": [...],
      "business_rule_alerts": [...]
    }
  ],
  "total": 2,
  "filters_applied": {
    "status": "CASTING",
    "brand_id": "M",
    "month": "2025-07",
    "campaign_ids": ["camp_001", "camp_002"]
  }
}
```

## 📊 필터 적용된 대시보드 요약

```http
GET /api/influencer-monitoring/dashboard/summary?brand_id=M&month=2025-07&days_range=30
```

**응답 예시:**
```json
{
  "period": "최근 30일",
  "filters_applied": {
    "brand_id": "M",
    "month": "2025-07",
    "campaign_ids": null
  },
  "campaigns": {
    "total": 12,
    "active": 8,
    "completed_this_period": 4
  },
  "influencers": {
    "total_participations": 156,
    "content_uploaded": 98,
    "awaiting_upload": 58
  },
  "delivery": {
    "total_entries": 134,
    "completed": 112,
    "in_progress": 22
  },
  "alerts": {
    "total_rules_triggered": 8,
    "high_priority": 5,
    "recent_alerts": [...]
  }
}
```

## 🎨 프론트엔드 연동 예시

### React 계층적 필터 컴포넌트

```typescript
interface FilterState {
  selectedBrand: string | null;
  selectedMonth: string | null;
  selectedCampaigns: string[];
}

const HierarchicalFilter: React.FC = () => {
  const [filterState, setFilterState] = useState<FilterState>({
    selectedBrand: null,
    selectedMonth: null,
    selectedCampaigns: []
  });
  
  const [filterOptions, setFilterOptions] = useState(null);
  
  // 전체 계층 데이터 로드
  useEffect(() => {
    fetch('/api/influencer-monitoring/filter-options/hierarchical')
      .then(res => res.json())
      .then(setFilterOptions);
  }, []);
  
  // 브랜드 선택 시
  const handleBrandSelect = (brandId: string) => {
    setFilterState({
      selectedBrand: brandId,
      selectedMonth: null,
      selectedCampaigns: []
    });
  };
  
  // 월 선택 시
  const handleMonthSelect = (month: string) => {
    setFilterState(prev => ({
      ...prev,
      selectedMonth: month,
      selectedCampaigns: []
    }));
  };
  
  // 캠페인 선택/해제
  const handleCampaignToggle = (campaignId: string) => {
    setFilterState(prev => ({
      ...prev,
      selectedCampaigns: prev.selectedCampaigns.includes(campaignId)
        ? prev.selectedCampaigns.filter(id => id !== campaignId)
        : [...prev.selectedCampaigns, campaignId]
    }));
  };
  
  // 필터된 데이터 조회
  useEffect(() => {
    const params = new URLSearchParams();
    if (filterState.selectedBrand) params.append('brand_id', filterState.selectedBrand);
    if (filterState.selectedMonth) params.append('month', filterState.selectedMonth);
    if (filterState.selectedCampaigns.length > 0) {
      params.append('campaign_ids', filterState.selectedCampaigns.join(','));
    }
    
    fetch(`/api/influencer-monitoring/campaigns?${params}`)
      .then(res => res.json())
      .then(updateDashboard);
  }, [filterState]);
  
  return (
    <div className="hierarchical-filter">
      {/* 브랜드 선택 */}
      <div className="filter-level">
        <h3>브랜드 선택</h3>
        {filterOptions?.hierarchical_filters.map(brand => (
          <button
            key={brand.brand_id}
            className={`filter-btn ${filterState.selectedBrand === brand.brand_id ? 'active' : ''}`}
            onClick={() => handleBrandSelect(brand.brand_id)}
          >
            {brand.brand_name} ({brand.total_campaigns})
          </button>
        ))}
      </div>
      
      {/* 월 선택 */}
      {filterState.selectedBrand && (
        <div className="filter-level">
          <h3>월 선택</h3>
          {getCurrentBrandData()?.months.map(month => (
            <button
              key={month.month_key}
              className={`filter-btn ${filterState.selectedMonth === month.month_key ? 'active' : ''}`}
              onClick={() => handleMonthSelect(month.month_key)}
            >
              {month.month_display} ({month.campaign_count})
            </button>
          ))}
        </div>
      )}
      
      {/* 캠페인 선택 */}
      {filterState.selectedMonth && (
        <div className="filter-level">
          <h3>캠페인 선택</h3>
          {getCurrentMonthCampaigns()?.map(campaign => (
            <label key={campaign.campaign_id} className="campaign-checkbox">
              <input
                type="checkbox"
                checked={filterState.selectedCampaigns.includes(campaign.campaign_id)}
                onChange={() => handleCampaignToggle(campaign.campaign_id)}
              />
              {campaign.camp_nm} ({campaign.status})
            </label>
          ))}
        </div>
      )}
    </div>
  );
};
```

### CSS 스타일 예시

```css
.hierarchical-filter {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-level {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 15px;
  background: white;
}

.filter-level h3 {
  margin-bottom: 10px;
  color: #495057;
  font-size: 14px;
  font-weight: 600;
}

.filter-btn {
  display: inline-block;
  margin: 4px 8px 4px 0;
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: white;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #007bff;
  color: #007bff;
}

.filter-btn.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.campaign-checkbox {
  display: block;
  margin: 8px 0;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
}

.campaign-checkbox:hover {
  background: #f8f9fa;
}
```

## 🔄 실사용 시나리오

### 시나리오 1: MLB 브랜드 7월 캠페인 모니터링
1. **브랜드 선택**: "MLB" 클릭
2. **월 선택**: "2025년 07월" 클릭  
3. **캠페인 선택**: 관심있는 2-3개 캠페인 체크
4. **결과**: 선택된 캠페인들의 상세 모니터링 대시보드 표시

### 시나리오 2: 전체 브랜드 특정 월 성과 비교
1. **월 필터만 적용**: `month=2025-07`
2. **브랜드별 성과 비교**: 모든 브랜드의 7월 성과 한눈에 확인

### 시나리오 3: 특정 캠페인들 집중 모니터링
1. **캠페인 ID 직접 지정**: `campaign_ids=camp_001,camp_005,camp_012`
2. **브랜드/월 무관하게** 선택된 캠페인들만 모니터링

## 📈 성능 최적화 팁

1. **계층적 데이터 캐싱**: `/filter-options/hierarchical` 응답을 5분간 캐시
2. **부분 로딩**: 브랜드 선택 후 해당 브랜드 월 데이터만 추가 로드  
3. **무한 스크롤**: 캠페인 목록이 많을 때 페이징 적용
4. **실시간 업데이트**: 선택된 필터에 해당하는 데이터만 WebSocket 구독

이제 사용자가 **브랜드 → 월 → 캠페인** 순서로 단계별로 필터링하면서 원하는 데이터를 정확하게 찾을 수 있는 강력한 시스템이 완성되었습니다! 🎉

