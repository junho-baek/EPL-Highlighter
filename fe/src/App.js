import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Live from "./pages/Live";
import Highlight from "./pages/Highlight";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/live" element={<Live />} />
        <Route path="/highlight" element={<Highlight />} />
      </Routes>
    </Router>
  );
}

export default App;
