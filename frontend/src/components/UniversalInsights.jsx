import React from 'react';

const UniversalInsights = () => {
    return (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Universal Insights</h2>
            <div style={{ flex: 1, background: '#fff', borderRadius: '8px', overflow: 'hidden' }}>
                <iframe 
                    src="http://localhost:8000/reports/universal_insights.html" 
                    title="Universal Insights"
                    style={{ width: '100%', height: '100%', border: 'none' }}
                />
            </div>
        </div>
    );
};

export default UniversalInsights;
