import React from 'react';
import styled from 'styled-components';

const HeaderBar = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #23304a;
  color: #fff;
  z-index: 10;
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 700;
  padding-left: 32px;
  letter-spacing: 1px;
`;

const Header: React.FC = () => (
  <HeaderBar>
    MARKETING AI AGENT
  </HeaderBar>
);

export default Header; 