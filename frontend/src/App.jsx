// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import StudySpace from './pages/StudySpace';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<div className="flex h-full items-center justify-center text-gray-400">Select a subject to start</div>} />
          <Route path="space/:spaceId" element={<StudySpace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
