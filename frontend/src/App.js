import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AlgoScriptEditor from "./components/AlgoScriptEditor";

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AlgoScriptEditor />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;