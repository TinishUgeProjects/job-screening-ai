import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import { Toaster, toast } from "react-hot-toast";
import "tailwindcss/tailwind.css";

const API_BASE_URL = "http://127.0.0.1:5000";

const Home = () => (
  <div className="flex flex-col items-center justify-center h-screen text-center">
    <h1 className="text-4xl font-bold">AI Job Screening System</h1>
    <p className="text-lg text-gray-600 mt-2">Upload job descriptions and resumes to find the best match.</p>
    <Link to="/upload-job" className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">Get Started</Link>
  </div>
);

const UploadJob = () => {
  const [jobTitle, setJobTitle] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch(`${API_BASE_URL}/upload_job`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_title: jobTitle, description }),
    });
    const data = await response.json();
    toast.success(data.message);
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <form className="w-1/3 p-6 bg-white shadow-md rounded-md" onSubmit={handleSubmit}>
        <h2 className="text-xl font-semibold mb-4">Upload Job Description</h2>
        <input className="w-full p-2 border rounded mb-2" type="text" placeholder="Job Title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required />
        <textarea className="w-full p-2 border rounded mb-4" placeholder="Job Description" value={description} onChange={(e) => setDescription(e.target.value)} required></textarea>
        <button className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600">Submit</button>
      </form>
    </div>
  );
};

const App = () => (
  <Router>
    <Toaster />
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/upload-job" element={<UploadJob />} />
    </Routes>
  </Router>
);

export default App;
