import styled from 'styled-components';

export const DashboardContainer = styled.div`
  padding: 0;
  max-width: 1600px;
  margin: 0 auto;
`;

export const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`;

export const DashboardTitle = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
`;

export const LiveIndicator = styled.div`
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

export const LiveDot = styled.div`
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

export const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
`;

export const DashboardSection = styled.div`
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

export const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
`;

export const Icon = styled.div`
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
`;

export const NotificationItem = styled.div`
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

export const NotificationIcon = styled.div`
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

export const NotificationContent = styled.div`
  flex: 1;
`;

export const NotificationTitle = styled.div`
  font-weight: 600;
  margin-bottom: 6px;
  color: #0f172a;
  font-size: 15px;
`;

export const NotificationDesc = styled.div`
  font-size: 14px;
  color: #64748b;
`;

export const ActionButton = styled.button`
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

export const FilterSection = styled.div`
  margin-top: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
`;

export const FilterTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
`;

export const FilterGroup = styled.div`
  margin-bottom: 20px;
`;

export const FilterGroupTitle = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 12px;
`;

export const RadioGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
`;

export const RadioItem = styled.label`
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

export const TreemapContainer = styled.div`
  height: 440px;
  background: #f8fafc;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const CircleItem = styled.div<{ size: number; x: number; y: number; color: string }>`
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

export const CircleName = styled.div`
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.4);
  line-height: 1.3;
  white-space: pre-line;
`;

export const CircleCount = styled.div`
  font-size: 14px;
  opacity: 0.95;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
`;

export const ReportPreview = styled.div`
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

export const TrendInsight = styled.div`
  background: linear-gradient(135deg, #e0f2fe, #b3e5fc);
  color: #0c4a6e;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #81d4fa;
  box-shadow: 0 4px 12px rgba(3, 105, 161, 0.1);
`;

export const TrendTitle = styled.div`
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 18px;
`;

export const TrendDesc = styled.div`
  font-size: 15px;
  opacity: 0.95;
  line-height: 1.5;
`;

export const TrendStats = styled.div`
  display: flex;
  gap: 32px;
  margin-top: 20px;
`;

export const TrendStat = styled.div`
  text-align: center;
`;

export const TrendStatValue = styled.div`
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
`;

export const TrendStatLabel = styled.div`
  font-size: 13px;
  opacity: 0.85;
  font-weight: 500;
`;

export const TagCloud = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
`;

export const Tag = styled.div`
  background: rgba(255,255,255,0.8);
  color: #0c4a6e;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.9);
  box-shadow: 0 2px 4px rgba(3, 105, 161, 0.1);
`;

export const TrendAnalysisGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
`;

export const TrendAnalysisCard = styled.div`
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

export const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  padding: 20px 0;
`;

export const ContentCard = styled.div`
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-4px);
  }
`;

export const ImageContainer = styled.div`
  position: relative;
  width: 100%;
  padding-top: 100%;
`;

export const ContentImage = styled.img`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

export const ContentInfo = styled.div`
  padding: 16px;
`;

export const InfluencerInfo = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 12px;
`;

export const Avatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
`;

export const Username = styled.span`
  font-weight: 600;
  color: #1a1a1a;
`;

export const PostDate = styled.span`
  margin-left: auto;
  color: #666;
  font-size: 0.9em;
`;

export const Stats = styled.div`
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 0.9em;
`;

export const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
`;

