// frontend/src/pages/Clean.jsx
import { useState } from 'react';
import axios from 'axios';
import Navbar from '../components/Navbar';

export default function Clean() {
  const [file, setFile] = useState(null);
  const [operation, setOperation] = useState("enhance");
  const [intensity, setIntensity] = useState(50);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");

  const stages = [
    "Loading image...",
    "Analyzing content...",
    "Applying enhancement...",
    "Finalizing result..."
  ];

  const handleClean = async () => {
    if (!file) return;
    const form = new FormData();
    form.append('image', file);
    form.append('operation', operation);
    if (operation !== "remove_bg") {
      form.append('intensity', intensity / 100);
    }

    setLoading(true);
    setProgress(0);
    setStage(stages[0]);

    let stageIndex = 0;
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 5;
        if (next >= (stageIndex + 1) * 25) {
          stageIndex++;
          if (stageIndex < stages.length) {
            setStage(stages[stageIndex]);
          }
        }
        if (next >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return next;
      });
    }, 150);

    try {
      const res = await axios.post('/api/clean', form);
      setResult(res.data);
      setProgress(100);
      setStage("Complete!");
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  const downloadCleanReport = (format) => {
    if (!result?.clean_id) return;
    window.location.href = `/api/clean_report/${result.clean_id}/${format}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-900 via-purple-900 to-pink-900">
      <Navbar />
      <div className="max-w-6xl mx-auto px-8 py-12">
        <h2 className="text-6xl font-bold text-center mb-16 text-pink-300 drop-shadow-lg">Image Cleaning & Enhancement</h2>
        
        <div className="glass p-16 max-w-3xl mx-auto text-center rounded-3xl shadow-2xl border border-pink-500/50">
          <label className="text-3xl block mb-8 text-pink-200">Upload Image to Process</label>
          <input
            type="file"
            accept="image/*"
            onChange={e => setFile(e.target.files[0])}
            className="block mx-auto text-lg file:mr-6 file:py-5 file:px-10 file:rounded-full file:bg-gradient-to-r file:from-pink-600 file:to-purple-600 file:text-white file:shadow-lg"
          />
          {file && <img src={URL.createObjectURL(file)} className="mt-10 rounded-2xl max-h-96 mx-auto shadow-2xl border-4 border-pink-500/50" />}
          
          <label className="text-3xl block mt-12 mb-6 text-pink-200">Select Operation</label>
          <select 
            value={operation} 
            onChange={e => setOperation(e.target.value)}
            className="bg-gradient-to-r from-pink-600/40 to-purple-600/40 backdrop-blur border border-pink-500/70 p-5 rounded-2xl text-2xl w-full max-w-lg mx-auto mb-10 focus:outline-none focus:ring-4 focus:ring-pink-500/80"
          >
            <option value="enhance">Advanced Enhance</option>
            <option value="remove_bg">Remove Background (Full Person)</option>
            <option value="brighten">Brighten Dark Image</option>
            <option value="denoise">Denoise Image</option>
            <option value="sharpen">Sharpen Image</option>
          </select>

          {operation !== "remove_bg" && (
            <div className="mt-10">
              <label className="text-3xl block mb-6 text-pink-200">Intensity Level</label>
              <input
                type="range"
                min="0"
                max="100"
                value={intensity}
                onChange={e => setIntensity(e.target.value)}
                className="w-full max-w-lg mx-auto h-4 bg-pink-900 rounded-lg appearance-none cursor-pointer slider-thumb"
                style={{ background: `linear-gradient(to right, #ec4899 0%, #ec4899 ${intensity}%, #4c1d95 ${intensity}%, #4c1d95 100%)` }}
              />
              <p className="mt-4 text-2xl text-pink-300 font-bold">{intensity}%</p>
            </div>
          )}
          
          <button onClick={handleClean} disabled={loading} className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 px-20 py-8 text-4xl rounded-full font-bold shadow-2xl hover:shadow-pink-500/60 transition transform hover:scale-105 mt-12">
            {loading ? "Processing..." : "Apply Operation"}
          </button>
        </div>

        {loading && (
          <div className="glass p-16 mt-20 text-center rounded-3xl border border-pink-500/50">
            <div className="inline-block relative w-48 h-48">
              <div className="absolute inset-0 rounded-full border-8 border-pink-500 border-t-transparent animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center text-5xl font-bold text-pink-300">
                {progress}%
              </div>
            </div>
            <p className="mt-8 text-3xl font-semibold text-pink-200">{stage}</p>
          </div>
        )}

        {result && (
          <div className="glass p-16 mt-20 rounded-3xl border border-pink-500/50 shadow-2xl">
            <h3 className="text-5xl font-bold text-center mb-16 text-pink-300">Original vs Processed</h3>
            <div className="grid md:grid-cols-2 gap-16">
              <div>
                <p className="text-3xl text-center mb-8">Original</p>
                <img src={`http://127.0.0.1:8000${result.original}`} className="rounded-3xl mx-auto max-h-96 shadow-2xl border-8 border-pink-500/50" />
              </div>
              <div>
                <p className="text-3xl text-center mb-8 text-pink-300">Processed ({operation})</p>
                <img src={`http://127.0.0.1:8000${result.cleaned}`} className="rounded-3xl mx-auto max-h-96 shadow-2xl border-8 border-pink-500" />
              </div>
            </div>
            
            <div className="text-center mt-20 space-x-12">
              <a href={`http://127.0.0.1:8000${result.cleaned}`} download className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 px-20 py-8 text-4xl rounded-full font-bold shadow-2xl hover:shadow-pink-500/60 inline-block transition transform hover:scale-105">
                Download Processed Image
              </a>
              <button onClick={() => downloadCleanReport('png')} className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 px-16 py-6 text-3xl rounded-full font-bold shadow-2xl hover:shadow-pink-500/60 transition transform hover:scale-105">
                Clean Report (PNG)
              </button>
              <button onClick={() => downloadCleanReport('pdf')} className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 px-16 py-6 text-3xl rounded-full font-bold shadow-2xl hover:shadow-pink-500/60 transition transform hover:scale-105">
                Clean Report (PDF)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}