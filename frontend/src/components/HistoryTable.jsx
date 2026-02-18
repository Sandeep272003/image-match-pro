import { useEffect, useState } from 'react';
import axios from 'axios';

export default function HistoryTable() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get('/api/history').then(res => setHistory(res.data));
  }, []);

  if (history.length === 0) return null;

  return (
    <div className="glass p-8 mt-12">
      <h3 className="text-3xl font-bold mb-6">Recent Activity</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left border-b border-white/20">
              <th className="py-4">Time</th>
              <th>Type</th>
              <th>Details</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {history.map(h => (
              <tr key={h.id} className="border-b border-white/10">
                <td className="py-4">{new Date(h.time).toLocaleString()}</td>
                <td className="capitalize">{h.type}</td>
                <td>{h.type === 'comparison' ? 'Two images compared' : 'Image cleaned'}</td>
                <td>{h.score ? `${h.score}%` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}