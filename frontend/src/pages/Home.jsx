import Navbar from '../components/Navbar';
import HistoryTable from '../components/HistoryTable';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="min-h-screen home-bg">
      <Navbar />
      <div className="max-w-6xl mx-auto px-8">
        <div className="text-center py-20">
          <h2 className="text-6xl font-bold mb-6 fade-in">Image Match Pro</h2>
          <p className="text-2xl opacity-90 mb-12 fade-in" style={{animationDelay: '0.3s'}}>Advanced AI-powered image comparison & cleaning — 100% offline & private</p>
          
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            <Link to="/compare" className="glass p-12 hover-lift fade-in" style={{animationDelay: '0.6s'}}>
              <h3 className="text-4xl font-bold mb-4">Image Comparison</h3>
              <p className="text-xl opacity-80">Compare two photos • Face match percentage • Simple previews</p>
            </Link>
            
            <Link to="/clean" className="glass p-12 hover-lift fade-in" style={{animationDelay: '0.9s'}}>
              <h3 className="text-4xl font-bold mb-4">Image Cleaning</h3>
              <p className="text-xl opacity-80">Enhance, remove background, brighten dark images, denoise, sharpen</p>
            </Link>
          </div>
        </div>
        
        <HistoryTable />
      </div>
    </div>
  );
}