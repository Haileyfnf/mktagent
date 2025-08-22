import React from 'react';
import { Outlet } from 'react-router-dom';
import styled from 'styled-components';
import Header from './Header';
import Sidebar from './Sidebar';

const Content = styled.main`
  padding: 60px 24px 40px 24px;    /* 상단: 헤더 높이, 좌우: 여백, 하단: 여백 */
  margin-left: 100px;              /* 사이드바 너비 */
  min-height: calc(100vh - 100px);  /* 전체 높이에서 패딩 제외 */
  background: #f8fafc;
`;

const Layout: React.FC = () => (
  <>
    <Header />
    <Sidebar />
    <Content>
      <Outlet />
    </Content>
  </>
);

export default Layout; 