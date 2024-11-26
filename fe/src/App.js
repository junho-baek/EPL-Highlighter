import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Live from "./pages/Live";
import Highlight from "./pages/Highlight";
import { ThemeProvider } from "./contexts/ThemeContext";

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/live" element={<Live />} />
          <Route path="/live/:gameId" element={<Live />} />
          <Route path="/highlight" element={<Highlight />} />
          <Route path="/highlight/:gameId" element={<Highlight />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
