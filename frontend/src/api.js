import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Status
  getStatus: () => client.get('/status'),
  
  // Logs
  getLogs: () => client.get('/logs'),
  
  // Execution
  runOrchestrator: (profile = 'scott_organizer') => 
    client.post(`/run?profile=${profile}`),
    
  // Knowledge Base
  searchKnowledge: (query, threshold = 1.3) => 
    client.get('/knowledge', { params: { query: query, threshold: threshold } }),
    
  // Configuration
  getConfig: () => client.get('/config'),
  setDryRun: (enabled) => client.post('/config/dry_run', { dry_run: enabled }),
  
  // Universal Insights
  getInsights: (limit = 50, sortBy = 'impact') =>
    client.get('/insights', { params: { limit, sort_by: sortBy } }),

  // Reports
  getReports: () => client.get('/reports/list'),
};
