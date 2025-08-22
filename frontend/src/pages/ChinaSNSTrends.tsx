import React from 'react';
import styled from 'styled-components';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const Content = styled.div`
  padding: 0;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
`;

const StatCard = styled.div`
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s;
  &:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transform: translateY(-2px);
  }
`;

const StatTitle = styled.div`
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 8px;
`;

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
`;

const StatChange = styled.div<{positive?: boolean}>`
  font-size: 13px;
  font-weight: 600;
  color: ${props => props.positive ? '#059669' : '#dc2626'};
`;

const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: 1.2fr 2.8fr;
  gap: 28px;
  margin-bottom: 32px;
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
`;

const CardHeader = styled.div`
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f1f5f9;
`;

const CardTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
`;

const CardContent = styled.div`
  padding: 20px 24px 24px;
`;

const TrendItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
  &:last-child { border-bottom: none; }
`;

const TrendInfo = styled.div`
  flex: 1;
`;

const TrendName = styled.div`
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
`;

const TrendMeta = styled.div`
  font-size: 13px;
  color: #64748b;
`;

const TrendScore = styled.div`
  font-size: 15px;
  font-weight: 600;
  color: #059669;
`;

const HashtagGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
`;

const HashtagCard = styled.div`
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: all 0.2s;
  &:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transform: translateY(-3px);
  }
`;

const HashtagName = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 8px;
`;

const HashtagGrowth = styled.div`
  font-size: 20px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 4px;
`;

const HashtagPosts = styled.div`
  font-size: 13px;
  color: #64748b;
`;

const CreatorGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
`;

const CreatorCard = styled.div`
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.2s;
  &:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transform: translateY(-2px);
  }
`;

const CreatorAvatar = styled.div`
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 20px;
`;

const CreatorName = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 6px;
`;

const CreatorFollowers = styled.div`
  font-size: 14px;
  color: #64748b;
  margin-bottom: 10px;
`;

const CreatorMatch = styled.div`
  font-size: 13px;
  font-weight: 500;
  color: #059669;
  background: #f0fdf4;
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 12px;
`;

const CreatorPlatforms = styled.div`
  display: flex;
  justify-content: center;
  gap: 10px;
`;

const PlatformBadge = styled.div<{type: string}>`
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  color: white;
  background: ${props => props.type === 'xiaohongshu' ? '#ff2442' : '#000'};
`;

const ChinaSNSTrends: React.FC = () => (
  <Content>
    {/* 주요 지표 */}
    <StatsGrid>
      <StatCard>
        <StatTitle>MLB 멘션</StatTitle>
        <StatValue>89.5K</StatValue>
        <StatChange positive>+18.3% ▲</StatChange>
      </StatCard>
      <StatCard>
        <StatTitle>수집 키워드</StatTitle>
        <StatValue>234</StatValue>
        <StatChange positive>+15개 ▲</StatChange>
      </StatCard>
      <StatCard>
        <StatTitle>급상승 키워드</StatTitle>
        <StatValue>92.7%</StatValue>
        <StatChange positive>+28% ▲</StatChange>
      </StatCard>
      <StatCard>
        <StatTitle>수집 채널</StatTitle>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ 
              width: '24px', 
              height: '24px', 
              borderRadius: '5px', 
              background: '#ff2442', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontSize: '14px', 
              fontWeight: 'bold', 
              color: 'white' 
            }}>小</div>
            <span style={{ fontSize: '20px', fontWeight: '600', color: '#0f172a' }}>샤오홍수</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ 
              width: '24px', 
              height: '24px', 
              borderRadius: '5px', 
              background: '#000', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontSize: '14px', 
              fontWeight: 'bold', 
              color: 'white' 
            }}>抖</div>
            <span style={{ fontSize: '20px', fontWeight: '600', color: '#0f172a' }}>도우인</span>
          </div>
        </div>
      </StatCard>
    </StatsGrid>

    {/* 대시보드 그리드 */}
    <DashboardGrid>
      {/* 트렌드 카드 */}
      <Card>
        <CardHeader>
          <CardTitle>브랜드 영향력</CardTitle>
        </CardHeader>
        <CardContent>
          <TrendItem>
            <TrendInfo>
              <TrendName>
                MLB 
                <span style={{ 
                  fontSize: '12px', 
                  color: '#059669', 
                  marginLeft: '8px',
                  fontWeight: '600'
                }}>▲ 2</span>
              </TrendName>
              <TrendMeta>18.7K 멘션 • 1일 전</TrendMeta>
            </TrendInfo>
            <TrendScore>+23%</TrendScore>
          </TrendItem>
          <TrendItem>
            <TrendInfo>
              <TrendName>
                Nike 
                <span style={{ 
                  fontSize: '12px', 
                  color: '#dc2626', 
                  marginLeft: '8px',
                  fontWeight: '600'
                }}>▼ 1</span>
              </TrendName>
              <TrendMeta>15.2K 멘션 • 1일 전</TrendMeta>
            </TrendInfo>
            <TrendScore>+15%</TrendScore>
          </TrendItem>
          <TrendItem>
            <TrendInfo>
              <TrendName>
                Salomon 
                <span style={{ 
                  fontSize: '12px', 
                  color: '#059669', 
                  marginLeft: '8px',
                  fontWeight: '600'
                }}>▲ 1</span>
              </TrendName>
              <TrendMeta>12.8K 멘션 • 1일 전</TrendMeta>
            </TrendInfo>
            <TrendScore>+12%</TrendScore>
          </TrendItem>
          <TrendItem>
            <TrendInfo>
              <TrendName>
                Arc'teryx 
                <span style={{ 
                  fontSize: '12px', 
                  color: '#64748b', 
                  marginLeft: '8px',
                  fontWeight: '600'
                }}>- 0</span>
              </TrendName>
              <TrendMeta>9.4K 멘션 • 1일 전</TrendMeta>
            </TrendInfo>
            <TrendScore>+9%</TrendScore>
          </TrendItem>
          <TrendItem>
            <TrendInfo>
              <TrendName>
                Adidas 
                <span style={{ 
                  fontSize: '12px', 
                  color: '#dc2626', 
                  marginLeft: '8px',
                  fontWeight: '600'
                }}>▼ 2</span>
              </TrendName>
              <TrendMeta>8.1K 멘션 • 1일 전</TrendMeta>
            </TrendInfo>
            <TrendScore>+5%</TrendScore>
          </TrendItem>
        </CardContent>
      </Card>

      {/* 인사이트 카드 */}
      <Card>
        <CardHeader>
          <CardTitle>최근 4주 브랜드 영향력</CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{ width: '100%', height: 280 }}>
            <Line
              data={{
                labels: ['1주차', '2주차', '3주차', '4주차'],
                datasets: [
                  {
                    label: 'MLB',
                    data: [45, 68, 85, 92],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                  },
                  {
                    label: 'Nike',
                    data: [75, 72, 68, 65],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                  },
                  {
                    label: 'Salomon',
                    data: [35, 55, 48, 72],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                  },
                  {
                    label: "Arc'teryx",
                    data: [60, 45, 38, 42],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                  },
                  {
                    label: 'Adidas',
                    data: [55, 42, 35, 28],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top' as const,
                    labels: {
                      usePointStyle: true,
                      padding: 20,
                    },
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                  },
                },
                scales: {
                  x: {
                    display: true,
                    title: {
                      display: true,
                      text: '주차',
                    },
                  },
                  y: {
                    display: true,
                    title: {
                      display: true,
                      text: '영향력 점수',
                    },
                    min: 0,
                    max: 100,
                  },
                },
                interaction: {
                  mode: 'nearest',
                  axis: 'x',
                  intersect: false,
                },
              }}
            />
          </div>
        </CardContent>
      </Card>
    </DashboardGrid>

    {/* 인기 해시태그 */}
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#0f172a' }}>
        인기 해시태그
      </h3>
      <HashtagGrid>
        <HashtagCard>
          <HashtagName>#Y2K패션</HashtagName>
          <HashtagGrowth>+245%</HashtagGrowth>
          <HashtagPosts>18.7K 포스트</HashtagPosts>
        </HashtagCard>
        <HashtagCard>
          <HashtagName>#크롭후디</HashtagName>
          <HashtagGrowth>+178%</HashtagGrowth>
          <HashtagPosts>15.2K 포스트</HashtagPosts>
        </HashtagCard>
        <HashtagCard>
          <HashtagName>#미니멀패션</HashtagName>
          <HashtagGrowth>+134%</HashtagGrowth>
          <HashtagPosts>12.8K 포스트</HashtagPosts>
        </HashtagCard>
        <HashtagCard>
          <HashtagName>#아테지어</HashtagName>
          <HashtagGrowth>+98%</HashtagGrowth>
          <HashtagPosts>9.4K 포스트</HashtagPosts>
        </HashtagCard>
        <HashtagCard>
          <HashtagName>#스트리트패션</HashtagName>
          <HashtagGrowth>+76%</HashtagGrowth>
          <HashtagPosts>8.1K 포스트</HashtagPosts>
        </HashtagCard>
        <HashtagCard>
          <HashtagName>#패션코디</HashtagName>
          <HashtagGrowth>+65%</HashtagGrowth>
          <HashtagPosts>7.3K 포스트</HashtagPosts>
        </HashtagCard>
      </HashtagGrid>
    </div>

    {/* 인플루언서 매칭 */}
    <div style={{ marginBottom: '40px' }}>
      <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#0f172a' }}>
        협업 추천 크리에이터
      </h3>
      <CreatorGrid>
        <CreatorCard>
          <CreatorAvatar>김</CreatorAvatar>
          <CreatorName>김패션</CreatorName>
          <CreatorFollowers>234K 팔로워</CreatorFollowers>
          <CreatorMatch>96% 매칭</CreatorMatch>
          <CreatorPlatforms>
            <PlatformBadge type="xiaohongshu">小</PlatformBadge>
            <PlatformBadge type="weibo">微</PlatformBadge>
          </CreatorPlatforms>
        </CreatorCard>
        <CreatorCard>
          <CreatorAvatar>박</CreatorAvatar>
          <CreatorName>박스타일</CreatorName>
          <CreatorFollowers>156K 팔로워</CreatorFollowers>
          <CreatorMatch>94% 매칭</CreatorMatch>
          <CreatorPlatforms>
            <PlatformBadge type="xiaohongshu">小</PlatformBadge>
            <PlatformBadge type="weibo">微</PlatformBadge>
          </CreatorPlatforms>
        </CreatorCard>
        <CreatorCard>
          <CreatorAvatar>이</CreatorAvatar>
          <CreatorName>이코디</CreatorName>
          <CreatorFollowers>98K 팔로워</CreatorFollowers>
          <CreatorMatch>91% 매칭</CreatorMatch>
          <CreatorPlatforms>
            <PlatformBadge type="xiaohongshu">小</PlatformBadge>
          </CreatorPlatforms>
        </CreatorCard>
        <CreatorCard>
          <CreatorAvatar>최</CreatorAvatar>
          <CreatorName>최패션</CreatorName>
          <CreatorFollowers>187K 팔로워</CreatorFollowers>
          <CreatorMatch>88% 매칭</CreatorMatch>
          <CreatorPlatforms>
            <PlatformBadge type="weibo">微</PlatformBadge>
          </CreatorPlatforms>
        </CreatorCard>
      </CreatorGrid>
    </div>
  </Content>
);

export default ChinaSNSTrends; 