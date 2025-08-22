import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import './InfluencerMonitoring.css';

const DashboardContainer = styled.div`
  padding: 0;
  max-width: 1600px;
  margin: 0 auto;
`;

const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`;

const DashboardTitle = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
`;

const LiveIndicator = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
`;

const LiveDot = styled.div`
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse 1.5s infinite;

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
`;

const DashboardSection = styled.div`
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transform: translateY(-2px);
  }
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
`;

const Icon = styled.div`
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
`;

// 사용되지 않는 스타일 컴포넌트들 제거됨

const NotificationItem = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
    transform: translateY(-1px);
  }
`;

const NotificationIcon = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
`;

const NotificationContent = styled.div`
  flex: 1;
`;

const NotificationTitle = styled.div`
  font-weight: 600;
  margin-bottom: 6px;
  color: #0f172a;
  font-size: 15px;
`;

const NotificationDesc = styled.div`
  font-size: 14px;
  color: #64748b;
`;

const ActionButton = styled.button`
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  }

  &.secondary {
    background: linear-gradient(135deg, #64748b, #475569);
  }

  &.secondary:hover {
    box-shadow: 0 4px 12px rgba(100, 116, 139, 0.4);
  }
`;

const FilterSection = styled.div`
  margin-top: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
`;

const FilterTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
`;

const FilterGroup = styled.div`
  margin-bottom: 20px;
`;

const FilterGroupTitle = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 12px;
`;

const RadioGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
`;

const RadioItem = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #64748b;

  &:hover {
    background: #f0f9ff;
  }

  input[type="radio"] {
    appearance: none;
    width: 16px;
    height: 16px;
    border: 2px solid #cbd5e1;
    border-radius: 50%;
    position: relative;
    cursor: pointer;
    transition: all 0.2s;

    &:checked {
      border-color: #3b82f6;
      background: #3b82f6;

      &::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 6px;
        height: 6px;
        background: white;
        border-radius: 50%;
      }
    }
  }

  &:has(input[type="radio"]:checked) {
    background: #f0f9ff;
    color: #1e40af;
    font-weight: 500;
  }
`;

const TreemapContainer = styled.div`
  height: 440px;
  background: #f8fafc;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const CircleItem = styled.div<{ size: number; x: number; y: number; color: string }>`
  position: absolute;
  width: ${props => props.size}px;
  height: ${props => props.size}px;
  left: ${props => props.x}px;
  top: ${props => props.y}px;
  border-radius: 50%;
  background: ${props => props.color};
  color: white;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
  border: 3px solid rgba(255,255,255,0.3);
  backdrop-filter: blur(10px);

  &:hover {
    transform: scale(1.05);
    z-index: 10;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  }
`;

const CircleName = styled.div`
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.4);
  line-height: 1.3;
  white-space: pre-line;
`;

const CircleCount = styled.div`
  font-size: 14px;
  opacity: 0.95;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
`;

const ReportPreview = styled.div`
  height: auto;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
  }
`;

const TrendInsight = styled.div`
  background: linear-gradient(135deg, #e0f2fe, #b3e5fc);
  color: #0c4a6e;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #81d4fa;
  box-shadow: 0 4px 12px rgba(3, 105, 161, 0.1);
`;

const TrendTitle = styled.div`
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 18px;
`;

const TrendDesc = styled.div`
  font-size: 15px;
  opacity: 0.95;
  line-height: 1.5;
`;

const TrendStats = styled.div`
  display: flex;
  gap: 32px;
  margin-top: 20px;
`;

const TrendStat = styled.div`
  text-align: center;
`;

const TrendStatValue = styled.div`
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
`;

const TrendStatLabel = styled.div`
  font-size: 13px;
  opacity: 0.85;
  font-weight: 500;
`;

const TagCloud = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
`;

const Tag = styled.div`
  background: rgba(255,255,255,0.8);
  color: #0c4a6e;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.9);
  box-shadow: 0 2px 4px rgba(3, 105, 161, 0.1);
`;

// FullWidth 스타일 컴포넌트 제거됨

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  padding: 20px 0;
`;

const ContentCard = styled.div`
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-4px);
  }
`;

const ImageContainer = styled.div`
  position: relative;
  width: 100%;
  padding-top: 100%; // 1:1 비율
`;

const ContentImage = styled.img`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

const ContentInfo = styled.div`
  padding: 16px;
`;

const InfluencerInfo = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 12px;
`;

const Avatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
`;

const Username = styled.span`
  font-weight: 600;
  color: #1a1a1a;
`;

const PostDate = styled.span`
  margin-left: auto;
  color: #666;
  font-size: 0.9em;
`;

const Stats = styled.div`
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 0.9em;
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
`;

const TrendAnalysisGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
`;

const TrendAnalysisCard = styled.div`
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
`;

interface FilterOptions {
  brand_id: string;
  brand_name: string;
  months: Array<{
    month_key: string;
    month_display: string;
    campaign_count: number;
    campaigns: Array<{
      campaign_id: string;
      camp_code: string;
      camp_nm: string;
      status: string;
    }>;
  }>;
}

interface ContentItem {
  id: number;
  username: string;
  avatar: string;
  image: string;
  likes: number;
  comments: number;
  views: number;
  postDate: string;
}

interface Campaign {
  campaign_id: string;
  camp_nm: string;
  camp_code: string;
  status: string;
  total_influencers: number;
  completion_rate: number;
  content_upload_rate: number;
  delivery_completion_rate: number;
  business_rule_alerts?: string[];
}

interface DashboardData {
  total: number;
  campaigns: Campaign[];
  latest_contents?: ContentItem[];
}

interface FilterState {
  selectedBrand: string | null;
  selectedMonth: string | null;
  selectedCampaigns: string[];
}

// 임시 컨텐츠 데이터
const mockLatestContents = [
  {
    id: 1,
    username: '@jenny_style',
    avatar: 'https://randomuser.me/api/portraits/women/1.jpg',
    image: '/images/discovery-report-preview.jpg',
    likes: 1234,
    comments: 56,
    views: 12000,
    postDate: '07-18'
  },
  {
    id: 2,
    username: '@travel_mtb',
    avatar: 'https://randomuser.me/api/portraits/women/2.jpg',
    image: '/images/discovery-report-preview.jpg',
    likes: 892,
    comments: 23,
    views: 8500,
    postDate: '07-18'
  }
];

const InfluencerMonitoring: React.FC = () => {
  const [circleItems, setCircleItems] = useState<Array<{
    name: string;
    value: number;
    color: string;
    size: number;
    x: number;
    y: number;
  }>>([]);

  const [filterOptions, setFilterOptions] = useState<FilterOptions[]>([]);
  const [filterState, setFilterState] = useState<FilterState>({
    selectedBrand: null,
    selectedMonth: null,
    selectedCampaigns: []
  });
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  const loadFilterOptions = async () => {
    try {
      // 계층적 필터 옵션 로드
      const response = await fetch('/api/influencer-monitoring/filter-options/hierarchical');
      const data = await response.json();
      setFilterOptions(data.hierarchical_filters || []);
      
      // 기본값으로 Discovery 브랜드 선택 (없으면 첫 번째 브랜드)
      if (data.hierarchical_filters && data.hierarchical_filters.length > 0) {
        const discoveryBrand = data.hierarchical_filters.find(
          (brand: FilterOptions) => brand.brand_name.includes('디스커버리') || brand.brand_name.toLowerCase().includes('discovery')
        );
        const defaultBrand = discoveryBrand || data.hierarchical_filters[0];
        
        setFilterState(prev => ({
          ...prev,
          selectedBrand: defaultBrand.brand_id
        }));
      }
    } catch (error) {
      console.error('필터 옵션 로드 실패:', error);
    }
  };

  const loadDashboardData = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterState.selectedBrand) params.append('brand_id', filterState.selectedBrand);
      if (filterState.selectedMonth) params.append('month', filterState.selectedMonth);
      if (filterState.selectedCampaigns.length > 0) {
        params.append('campaign_ids', filterState.selectedCampaigns.join(','));
      }
      
      const response = await fetch(`/api/influencer-monitoring/campaigns?${params}`);
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
    }
  }, [filterState]);

  useEffect(() => {
    createCirclePack();
    loadFilterOptions();
    
    // 실시간 데이터 업데이트 시뮬레이션
    const interval = setInterval(() => {
      // 좋아요 수 랜덤 업데이트
      const statsElements = document.querySelectorAll('.content-stats .stat');
      statsElements.forEach(stat => {
        if (stat.textContent?.includes('❤️')) {
          const current = parseInt(stat.textContent.match(/\d+/)?.[0] || '0');
          const newValue = current + Math.floor(Math.random() * 10);
          stat.textContent = `❤️ ${newValue.toLocaleString()}`;
        }
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // 필터 변경 시 대시보드 데이터 업데이트
  useEffect(() => {
    if (filterState.selectedBrand) {
      loadDashboardData();
    }
  }, [filterState, loadDashboardData]);

  const handleBrandSelect = (brandId: string) => {
    setFilterState({
      selectedBrand: brandId,
      selectedMonth: null,
      selectedCampaigns: []
    });
  };

  const handleMonthSelect = (month: string) => {
    setFilterState(prev => ({
      ...prev,
      selectedMonth: month,
      selectedCampaigns: []
    }));
  };

  const handleCampaignToggle = (campaignId: string) => {
    setFilterState(prev => ({
      ...prev,
      selectedCampaigns: prev.selectedCampaigns.includes(campaignId)
        ? prev.selectedCampaigns.filter(id => id !== campaignId)
        : [...prev.selectedCampaigns, campaignId]
    }));
  };

  const getCurrentBrandData = () => {
    return filterOptions.find(brand => brand.brand_id === filterState.selectedBrand);
  };

  const getCurrentMonthCampaigns = () => {
    const brandData = getCurrentBrandData();
    if (!brandData || !filterState.selectedMonth) return [];
    
    const monthData = brandData.months.find(month => month.month_key === filterState.selectedMonth);
    return monthData?.campaigns || [];
  };

  const createCirclePack = () => {
    const items = [
      { name: '티셔츠', value: 120, color: 'linear-gradient(135deg, #a5b4fc, #818cf8)' },
      { name: '슬라이드', value: 65, color: 'linear-gradient(135deg, #86efac, #6ee7b7)' },
      { name: '슬링백', value: 35, color: 'linear-gradient(135deg, #fcd34d, #fbbf24)' },
      { name: '모자', value: 8, color: 'linear-gradient(135deg, #fca5a5, #f87171)' },
      { name: '스윔웨어', value: 22, color: 'linear-gradient(135deg, #c4b5fd, #a78bfa)' }
    ];

    const containerWidth = 400; // 예상 컨테이너 너비
    const containerHeight = 320;
    const centerX = containerWidth * 0.8; // 우측으로 더 이동 (0.6 → 0.8)
    const centerY = containerHeight * 0.65; // 아래로 더 이동 (0.55 → 0.65)

    // 값의 차이를 더 크게 반영하기 위해 최대값 기준으로 조정
    const maxValue = Math.max(...items.map(item => item.value));
    const maxRadius = Math.min(containerWidth, containerHeight) * 0.35; // 더 크게
    const minRadius = maxRadius * 0.2; // 최소 반지름 조정

    const circleItems = items.map((item, index) => {
      // 값에 따른 반지름 계산 (더 큰 차이)
      const radius = minRadius + (maxRadius - minRadius) * (item.value / maxValue);
      
      // 우측으로 더 넓게 배치
      const angle = (index * 2 * Math.PI) / items.length;
      const distance = Math.min(containerWidth, containerHeight) * 0.4; // 거리를 더 늘려서 더 넓게 배치
      const x = centerX + Math.cos(angle) * distance - radius;
      const y = centerY + Math.sin(angle) * distance - radius;

      return {
        ...item,
        size: radius * 2,
        x,
        y
      };
    });

    // 중앙에 가장 큰 원 추가 (전체 합계)
    const totalValue = items.reduce((sum, item) => sum + item.value, 0);
    const centerRadius = maxRadius * 1.4; // 중앙 원 크기 확대
    circleItems.push({
      name: '전체',
      value: totalValue,
      color: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
      size: centerRadius,
      x: centerX - centerRadius / 2,
      y: centerY - centerRadius / 2
    });

    setCircleItems(circleItems);
  };

  const sendEmailAlert = () => {
    alert('📧 광고 집행 제안 메일이 실무자에게 발송되었습니다.');
  };

  const sendFollowUpDM = () => {
    alert('💬 미업로드 인플루언서 3명에게 팔로업 DM이 발송되었습니다.\n\n메시지: "안녕하세요! 디스커버리 익스페디션 협찬 콘텐츠 업로드 일정 확인 부탁드립니다 :)"');
  };

  const sendGuidelineDM = () => {
    alert('⚠️ 가이드라인 위반 인플루언서에게 수정 요청 DM이 발송되었습니다.\n\n메시지: "안녕하세요! 업로드해주신 콘텐츠에 #디스커버리 해시태그 추가 부탁드립니다."');
  };

  const generateReport = () => {
    alert('📊 주간 성과 리포트 PPT가 생성되었습니다. 다운로드를 시작합니다.');
  };

  return (
    <DashboardContainer>
      <DashboardHeader>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <RadioGroup>
              {filterOptions.map(brand => (
                <RadioItem key={brand.brand_id}>
                  <input 
                    type="radio" 
                    name="brand" 
                    value={brand.brand_id}
                    checked={filterState.selectedBrand === brand.brand_id}
                    onChange={() => handleBrandSelect(brand.brand_id)}
                  />
                  {brand.brand_name === '디스커버리 익스페디션' ? '디스커버리' : 
                   brand.brand_name === 'MLB' ? 'MLB' :
                   brand.brand_name.includes('키즈') ? brand.brand_name.replace(' 키즈', ' 키즈') :
                   brand.brand_name}
                </RadioItem>
              ))}
            </RadioGroup>
        </div>
        <LiveIndicator>
          <LiveDot />
          AI 액션 ON
        </LiveIndicator>
      </DashboardHeader>

      {/* 세부 필터 시스템 */}
      {filterState.selectedBrand && (
        <FilterSection>
          <FilterTitle>🔍 세부 필터</FilterTitle>
          
          {/* 월 선택 */}
          {getCurrentBrandData()?.months && (getCurrentBrandData()?.months?.length || 0) > 0 && (
            <FilterGroup>
              <FilterGroupTitle>월 선택</FilterGroupTitle>
              <RadioGroup>
                <RadioItem>
                  <input 
                    type="radio" 
                    name="month" 
                    value=""
                    checked={!filterState.selectedMonth}
                    onChange={() => setFilterState(prev => ({ ...prev, selectedMonth: null, selectedCampaigns: [] }))}
                  />
                  전체
                </RadioItem>
                {getCurrentBrandData()?.months.map(month => (
                  <RadioItem key={month.month_key}>
                    <input 
                      type="radio" 
                      name="month" 
                      value={month.month_key}
                      checked={filterState.selectedMonth === month.month_key}
                      onChange={() => handleMonthSelect(month.month_key)}
                    />
                    {month.month_display} ({month.campaign_count}개)
                  </RadioItem>
                ))}
              </RadioGroup>
            </FilterGroup>
          )}

          {/* 캠페인 선택 */}
          {filterState.selectedMonth && getCurrentMonthCampaigns().length > 0 && (
            <FilterGroup>
              <FilterGroupTitle>캠페인 선택 (다중 선택 가능)</FilterGroupTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                {getCurrentMonthCampaigns().map(campaign => (
                  <label key={campaign.campaign_id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    background: 'white',
                    borderRadius: '8px',
                    border: filterState.selectedCampaigns.includes(campaign.campaign_id) ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}>
                    <input
                      type="checkbox"
                      checked={filterState.selectedCampaigns.includes(campaign.campaign_id)}
                      onChange={() => handleCampaignToggle(campaign.campaign_id)}
                      style={{
                        width: '16px',
                        height: '16px',
                        accentColor: '#3b82f6'
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: '#0f172a' }}>
                        {campaign.camp_nm}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>
                        {campaign.camp_code} • {campaign.status}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </FilterGroup>
          )}

          {/* 필터 적용 현황 */}
          {(filterState.selectedMonth || filterState.selectedCampaigns.length > 0) && (
            <div style={{
              marginTop: '16px',
              padding: '12px',
              background: '#f0f9ff',
              borderRadius: '8px',
              border: '1px solid #bae6fd'
            }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#0c4a6e', marginBottom: '8px' }}>
                📌 적용된 세부 필터
              </div>
              <div style={{ fontSize: '12px', color: '#075985', lineHeight: '1.4' }}>
                브랜드: {getCurrentBrandData()?.brand_name}
                {filterState.selectedMonth && ` • 월: ${getCurrentBrandData()?.months.find(m => m.month_key === filterState.selectedMonth)?.month_display}`}
                {filterState.selectedCampaigns.length > 0 && ` • 선택된 캠페인: ${filterState.selectedCampaigns.length}개`}
              </div>
            </div>
          )}
        </FilterSection>
      )}

      <DashboardGrid>
        {/* 필터된 캠페인 데이터 */}
        <DashboardSection>
          <SectionTitle>
            <Icon />
            캠페인 업데이트 {dashboardData?.total && `(${dashboardData.total}개)`}
          </SectionTitle>
          
          {dashboardData && dashboardData.campaigns && dashboardData.campaigns.length > 0 ? (
            <>
              <ContentGrid>
                {(dashboardData?.latest_contents || mockLatestContents).map((content: ContentItem) => (
                  <ContentCard key={content.id}>
                    <ImageContainer>
                      <ContentImage src={content.image} alt="Content preview" />
                    </ImageContainer>
                    <ContentInfo>
                      <InfluencerInfo>
                        <Avatar src={content.avatar} alt={content.username} />
                        <Username>{content.username}</Username>
                        <PostDate>{content.postDate}</PostDate>
                      </InfluencerInfo>
                      <Stats>
                        <StatItem>
                          <i className="fas fa-heart" />
                          {content.likes.toLocaleString()}
                        </StatItem>
                        <StatItem>
                          <i className="fas fa-comment" />
                          {content.comments.toLocaleString()}
                        </StatItem>
                        <StatItem>
                          <i className="fas fa-eye" />
                          {content.views.toLocaleString()}
                        </StatItem>
                      </Stats>
                    </ContentInfo>
                  </ContentCard>
                ))}
              </ContentGrid>
              <div style={{ 
                display: 'grid', 
                gap: '16px',
                maxHeight: '450px',
                overflowY: 'auto',
                marginTop: '24px'
              }}>
                {dashboardData.campaigns.slice(0, 4).map((campaign: Campaign, index: number) => (
                <div key={campaign.campaign_id} style={{
                  background: '#f8fafc',
                  borderRadius: '12px',
                  padding: '16px',
                  border: '1px solid #e2e8f0'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '12px'
                  }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: '#0f172a', marginBottom: '4px' }}>
                        {campaign.camp_nm}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>
                        상태: {campaign.status} • 총 인플루언서: {campaign.total_influencers}명
                      </div>
                    </div>
                    <div style={{
                      background: campaign.status === 'COMPLETE' ? '#dcfce7' : '#fef3c7',
                      color: campaign.status === 'COMPLETE' ? '#166534' : '#92400e',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '600'
                    }}>
                      {campaign.status}
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#64748b' }}>완료율: </span>
                      <span style={{ fontWeight: '600', color: '#059669' }}>{campaign.completion_rate}%</span>
                    </div>
                    <div>
                      <span style={{ color: '#64748b' }}>업로드율: </span>
                      <span style={{ fontWeight: '600', color: '#0284c7' }}>{campaign.content_upload_rate}%</span>
                    </div>
                    <div>
                      <span style={{ color: '#64748b' }}>배송율: </span>
                      <span style={{ fontWeight: '600', color: '#7c3aed' }}>{campaign.delivery_completion_rate}%</span>
                    </div>
                  </div>

                  {campaign.business_rule_alerts && campaign.business_rule_alerts.length > 0 && (
                    <div style={{
                      marginTop: '12px',
                      padding: '8px',
                      background: '#fef2f2',
                      borderRadius: '6px',
                      border: '1px solid #fecaca'
                    }}>
                      <div style={{ fontSize: '11px', color: '#991b1b', fontWeight: '600' }}>
                        ⚠️ 알림 {campaign.business_rule_alerts.length}개
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              color: '#64748b'
            }}>
              {filterState.selectedBrand ? '선택된 필터에 해당하는 캠페인이 없습니다.' : '브랜드를 선택해주세요.'}
            </div>
          )}
        </DashboardSection>

        {/* 실무자 알림 & 액션봇 */} 
        <DashboardSection>
          <SectionTitle>
            <Icon />
            알림 & 추가 액션
          </SectionTitle>
          
          {dashboardData && dashboardData.campaigns ? (
            <>
              {/* 필터된 데이터 기반 알림 */}
              <NotificationItem>
                <NotificationIcon>📊</NotificationIcon>
                <NotificationContent>
                  <NotificationTitle>선택된 필터 요약</NotificationTitle>
                  <NotificationDesc>
                    총 {dashboardData.total}개 캠페인 • 평균 완료율 {
                      dashboardData.campaigns.length > 0 
                        ? Math.round(dashboardData.campaigns.reduce((sum: number, c: any) => sum + c.completion_rate, 0) / dashboardData.campaigns.length)
                        : 0
                    }%
                  </NotificationDesc>
                </NotificationContent>
                <ActionButton onClick={generateReport}>리포트 생성</ActionButton>
              </NotificationItem>

              {/* 고성과 캠페인 알림 */}
              {dashboardData.campaigns.some((c: Campaign) => c.completion_rate > 80) && (
                <NotificationItem>
                  <NotificationIcon>🚀</NotificationIcon>
                  <NotificationContent>
                    <NotificationTitle>높은 성과 캠페인 감지</NotificationTitle>
                    <NotificationDesc>
                      {dashboardData.campaigns.filter((c: Campaign) => c.completion_rate > 80).length}개 캠페인이 80% 이상 완료율 달성
                    </NotificationDesc>
                  </NotificationContent>
                  <ActionButton onClick={sendEmailAlert}>광고 집행 제안</ActionButton>
                </NotificationItem>
              )}

              {/* 저성과 캠페인 알림 */}
              {dashboardData.campaigns.some((c: Campaign) => c.completion_rate < 30) && (
                <NotificationItem>
                  <NotificationIcon>⏰</NotificationIcon>
                  <NotificationContent>
                    <NotificationTitle>주의 필요 캠페인</NotificationTitle>
                    <NotificationDesc>
                      {dashboardData.campaigns.filter((c: Campaign) => c.completion_rate < 30).length}개 캠페인의 완료율이 30% 미만
                    </NotificationDesc>
                  </NotificationContent>
                  <ActionButton className="secondary" onClick={sendFollowUpDM}>팔로업 DM</ActionButton>
                </NotificationItem>
              )}

              {/* 비즈니스 룰 알림 */}
              {dashboardData.campaigns.some((c: Campaign) => c.business_rule_alerts && c.business_rule_alerts.length > 0) && (
                <NotificationItem>
                  <NotificationIcon>⚠️</NotificationIcon>
                  <NotificationContent>
                    <NotificationTitle>비즈니스 룰 위반 감지</NotificationTitle>
                    <NotificationDesc>
                      {dashboardData.campaigns.reduce((sum: number, c: Campaign) => sum + (c.business_rule_alerts?.length || 0), 0)}개 알림 • 즉시 조치 필요
                    </NotificationDesc>
                  </NotificationContent>
                  <ActionButton className="secondary" onClick={sendGuidelineDM}>규칙 안내 DM</ActionButton>
                </NotificationItem>
              )}
            </>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              color: '#64748b'
            }}>
              필터를 선택하면 관련 알림이 표시됩니다.
            </div>
          )}
        </DashboardSection>

        {/* 아이템별 콘텐츠 수급 현황 */}
        <DashboardSection>
          <SectionTitle>
            <Icon />
            아이템별 콘텐츠 수급 현황
          </SectionTitle>
          <TreemapContainer>
            {circleItems.map((item, index) => (
              <CircleItem
                key={index}
                size={item.size}
                x={item.x}
                y={item.y}
                color={item.color}
              >
                <CircleName>{item.name}</CircleName>
                <CircleCount>{item.value}개</CircleCount>
              </CircleItem>
            ))}
          </TreemapContainer>
        </DashboardSection>

        {/* 일일/주간 성과 리포트 */}
        <DashboardSection>
          <SectionTitle>
            <Icon />
            성과 리포트 자동 생성
          </SectionTitle>
          <ReportPreview onClick={generateReport}>
            <div style={{ textAlign: 'center' }}>
              <img 
                src="/images/discovery-report-preview.jpg" 
                alt="Discovery 25SS 6월 REVIEW 리포트 프리뷰"
                style={{
                  width: '100%',
                  maxWidth: '400px',
                  height: '225px', // 16:9 비율 (400 * 9/16 ≈ 225)
                  objectFit: 'cover',
                  borderRadius: '8px',
                  margin: '0 auto 16px',
                  border: '1px solid #e2e8f0',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}
              />
              <div style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>
                📊 Discovery 25SS 6월 REVIEW
              </div>
              <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '16px' }}>
                통합인플루언서마케팅 KPI 요약
              </div>
              <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                <div>• ENG: 85,584</div>
                <div>• CONTENTS: 96개</div>
                <div>• IMP: 4.5M</div>
              </div>
              <div style={{
                background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                color: 'white',
                padding: '10px 20px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'inline-block'
              }}>
                PPT 다운로드
              </div>
            </div>
          </ReportPreview>
        </DashboardSection>
      </DashboardGrid>

      {/* 콘텐츠 트렌드 분석 (전체 너비) */}
      <DashboardSection style={{ gridColumn: '1 / -1' }}>
        <SectionTitle>
          <Icon />
          콘텐츠 이미지 라벨링 & 콘텐츠 분석
        </SectionTitle>
        
        <TrendInsight>
          <TrendTitle>🔥 이번 주 HOT 콘텐츠</TrendTitle>
          <TrendDesc>'수영장 + 크롭티 + 웨이브 헤어' 조합이 평균 대비 인게이지먼트 +38% 상승</TrendDesc>
          <TrendStats>
            <TrendStat>
              <TrendStatValue>+38%</TrendStatValue>
              <TrendStatLabel>인게이지먼트</TrendStatLabel>
            </TrendStat>
            <TrendStat>
              <TrendStatValue>156</TrendStatValue>
              <TrendStatLabel>관련 콘텐츠</TrendStatLabel>
            </TrendStat>
            <TrendStat>
              <TrendStatValue>24</TrendStatValue>
              <TrendStatLabel>참여 인플루언서</TrendStatLabel>
            </TrendStat>
          </TrendStats>
          <TagCloud>
            <Tag>#수영장</Tag>
            <Tag>#크롭티</Tag>
            <Tag>#웨이브헤어</Tag>
            <Tag>#여름스타일</Tag>
            <Tag>#아웃도어</Tag>
            <Tag>#캐주얼룩</Tag>
          </TagCloud>
        </TrendInsight>

        <TrendAnalysisGrid>
          <TrendAnalysisCard>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#3b82f6', marginBottom: '8px' }}>
              포즈 분석
            </div>
            <div style={{ fontSize: '15px', color: '#64748b' }}>
              측면 포즈 +22% ↗️
            </div>
          </TrendAnalysisCard>
          <TrendAnalysisCard>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#3b82f6', marginBottom: '8px' }}>
              배경 분석
            </div>
            <div style={{ fontSize: '15px', color: '#64748b' }}>
              자연 배경 +31% ↗️
            </div>
          </TrendAnalysisCard>
          <TrendAnalysisCard>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#3b82f6', marginBottom: '8px' }}>
              컬러 분석
            </div>
            <div style={{ fontSize: '15px', color: '#64748b' }}>
              파스텔톤 +19% ↗️
            </div>
          </TrendAnalysisCard>
        </TrendAnalysisGrid>
      </DashboardSection>
    </DashboardContainer>
  );
};

export default InfluencerMonitoring;