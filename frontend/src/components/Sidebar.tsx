import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';

const SidebarWrap = styled.aside`
  position: fixed;
  top: 60px; /* 헤더 높이 */
  left: 0;
  width: 100px;
  height: calc(100vh - 60px);
  background: #2d3a54;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
  box-sizing: border-box;
  z-index: 5;
`;

const SidebarItem = styled(Link)`
  width: 100px;
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8b95a5;
  cursor: pointer;
  transition: color 0.3s;
  text-decoration: none;
  font-size: 15px;

  &.active {
    color: #3b82f6;
  }
  &:hover {
    color: #fff;
  }
  span {
    font-size: 11px;
    text-align: center;
    margin-top: 3px;
    white-space: nowrap;
  }
`;

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <SidebarWrap>
      <SidebarItem 
        to="/news-monitoring" 
        className={location.pathname === '/news-monitoring' ? 'active' : ''}
      >
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
          <path d="M280-280q17 0 28.5-11.5T320-320q0-17-11.5-28.5T280-360q-17 0-28.5 11.5T240-320q0 17 11.5 28.5T280-280Zm-40-160h80v-240h-80v240Zm200 160h280v-80H440v80Zm0-160h280v-80H440v80Zm0-160h280v-80H440v80ZM160-120q-33 0-56.5-23.5T80-200v-560q0-33 23.5-56.5T160-840h640q33 0 56.5 23.5T880-760v560q0 33-23.5 56.5T800-120H160Zm0-80h640v-560H160v560Zm0 0v-560 560Z"/>
        </svg>
        <span>뉴스 모니터링</span>
      </SidebarItem>
      <SidebarItem 
        to="/china-sns-trends" 
        className={location.pathname === '/china-sns-trends' ? 'active' : ''}
      >
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
          <path d="M320-414v-306h120v306l-60-56-60 56Zm200 60v-526h120v406L520-354ZM120-216v-344h120v224L120-216Zm0 98 258-258 142 122 224-224h-64v-80h200v200h-80v-64L524-146 382-268 232-118H120Z"/>
        </svg>
        <span>중국 SNS 트렌드</span>
      </SidebarItem>
      <SidebarItem 
        to="/influencer-monitoring" 
        className={location.pathname === '/influencer-monitoring' ? 'active' : ''}
      >
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
          <path d="M480-480q-50 0-85-35t-35-85q0-50 35-85t85-35q50 0 85 35t35 85q0 50-35 85t-85 35Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm0 440q-75 0-140.5-28.5t-114-77q-48.5-48.5-77-114T120-480q0-75 28.5-140.5t77-114q48.5-48.5 114-77T480-840q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-480q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-120Zm0-80q125 0 212.5-87.5T780-480q0-125-87.5-212.5T480-780q-125 0-212.5 87.5T180-480q0 125 87.5 212.5T480-180Zm0-300Z"/>
        </svg>
        <span>인플루언서<br/>모니터링</span>
      </SidebarItem>
      <SidebarItem 
        to="/browser-settings" 
        className={location.pathname === '/browser-settings' ? 'active' : ''}
      >
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
          <path d="M480-480ZM370-80l-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-74 56q-22-11-45-18.5T714-558l63-48-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q17 17 36.5 30.5T400-275q1 57 23.5 107T484-80H370Zm41-279q6-20 14.5-38.5T445-433q-11-8-17-20.5t-6-26.5q0-25 17.5-42.5T482-540q14 0 27 6.5t21 17.5q17-11 35-19.5t38-13.5q-18-32-50-51.5T482-620q-59 0-99.5 41T342-480q0 38 18.5 70.5T411-359Zm279 199 120-120-120-120-28 28 72 72H560v40h163l-71 72 28 28Zm0 80q-83 0-141.5-58.5T480-280q0-83 58.5-141.5T680-480q83 0 141.5 58.5T880-280q0 83-58.5 141.5T680-80Z"/>
        </svg>
        <span>브라우저 설정</span>
      </SidebarItem>
    </SidebarWrap>
  );
};

export default Sidebar; 