import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Cortex from './components/Cortex';
import Synapse from './components/Synapse';
import UniversalInsights from './components/UniversalInsights';
import { AnimatePresence } from 'framer-motion';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="cortex" element={<Cortex />} />
        <Route path="insights" element={<UniversalInsights />} />
        <Route path="synapse" element={<Synapse />} />
      </Route>
    </Routes>
  );
}

export default App;
