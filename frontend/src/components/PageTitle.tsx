import React from 'react';

interface PageTitleProps {
  title: string;
}

const PageTitle: React.FC<PageTitleProps> = ({ title }) => (
  <h2 style={{ fontSize: '22px', fontWeight: 600, color: '#23304a', marginBottom: '24px' }}>{title}</h2>
);

export default PageTitle; 