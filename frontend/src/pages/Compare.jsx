import { useState } from 'react';
import axios from 'axios';
import Navbar from '../components/Navbar';

export default function Compare() {
  const [files, setFiles] = useState({ img1: null, img2: null });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleCompare = async () => {
    if (!files.img1 || !files.img2) return;
    const form = new FormData();
    form.append('image1', files.img1);
    form.append('image2', files.img2);

    setLoading(true);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const res = await axios.post('/api/compare', form);
      setResult(res.data);
      setProgress(100);
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  const downloadReport = (format) => {
    if (!result?.comparison_id) return;
    window.location.href = `/api/report/${result.comparison_id}/${format}`;
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-8 py-12">
        <h2 className="text-5xl font-bold text-center mb-12">Image Comparison</h2>
        
        <div className="grid md:grid-cols-2 gap-12 mb-16">
          {['img1', 'img2'].map((key, i) => (
            <div key={key} className="glass p-8">
              <label className="text-2xl block mb-4">Image {i+1}</label>
              <input
                type="file"
                accept="image/*"
                onChange={e => setFiles({...files, [key]: e.target.files[0]})}
                className="block w-full text-lg file:mr-6 file:py-4 file:px-8 file:rounded-full file:bg-gradient-to-r file:from-purple-600 file:to-pink-600"
              />
              {files[key] && <img src={URL.createObjectURL(files[key])} className="mt-6 rounded-xl max-h-80 mx-auto" />}
            </div>
          ))}
        </div>
        
        <div className="text-center mb-16">
          <button onClick={handleCompare} disabled={loading} className="btn-gradient px-16 py-6 text-3xl rounded-full font-bold">
            {loading ? "Analyzing..." : "Compare Images"}
          </button>
        </div>

        {loading && (
          <div className="glass p-12 text-center">
            <div className="inline-block relative w-32 h-32">
              <div className="absolute inset-0 rounded-full border-4 border-t-pink-600 animate-spin" style={{ borderTopColor: 'transparent' }}></div>
              <div className="absolute inset-0 flex items-center justify-center text-3xl font-bold">
                {progress}%
              </div>
            </div>
            <p className="mt-4 text-2xl">Processing Image Comparison...</p>
          </div>
        )}

        {result && (
          <div className="glass p-12">
            <h3 className="text-5xl font-bold text-center mb-8">
              Face Match {result.face_match}%
            </h3>

            <div className="grid md:grid-cols-2 gap-12 mb-12">
              <img src={`http://127.0.0.1:8000${result.image1}`} className="rounded-2xl" alt="Image 1" />
              <img src={`http://127.0.0.1:8000${result.image2}`} className="rounded-2xl" alt="Image 2" />
            </div>

            <div className="grid md:grid-cols-4 gap-4 mb-12">
              <div className="glass p-4 text-center">
                <p className="text-sm opacity-70">Face Structure</p>
                <p className="text-2xl font-bold">{result.face_structure_similarity}%</p>
              </div>
              <div className="glass p-4 text-center">
                <p className="text-sm opacity-70">Feature Match</p>
                <p className="text-2xl font-bold">{result.feature_similarity}%</p>
              </div>
              <div className="glass p-4 text-center">
                <p className="text-sm opacity-70">SSIM</p>
                <p className="text-2xl font-bold">{result.ssim_similarity}%</p>
              </div>
              <div className="glass p-4 text-center">
                <p className="text-sm opacity-70">PSNR</p>
                <p className="text-2xl font-bold">{result.psnr_similarity}%</p>
              </div>
            </div>

            <div className="text-center space-x-8">
              <button onClick={() => downloadReport('png')} className="btn-gradient px-12 py-5 text-2xl rounded-full">
                Download Report (PNG)
              </button>
              <button onClick={() => downloadReport('pdf')} className="btn-gradient px-12 py-5 text-2xl rounded-full">
                Download Report (PDF)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}