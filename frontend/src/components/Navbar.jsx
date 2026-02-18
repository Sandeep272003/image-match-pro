import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="glass p-6 mb-10">
      <div className="max-w-6xl mx-auto flex justify-between items-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          Image Match Pro
        </h1>
        <div className="space-x-8">
          <Link to="/" className="text-xl hover:text-pink-400 transition">Home</Link>
          <Link to="/compare" className="text-xl hover:text-pink-400 transition">Compare</Link>
          <Link to="/clean" className="text-xl hover:text-pink-400 transition">Clean</Link>
        </div>
      </div>
    </nav>
  );
}