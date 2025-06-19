import { useState } from 'react';

const ProtocolUploader = () => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // This component is a placeholder for Sprint 2
    // Actual implementation will come later
    
    alert('Protocol uploader will be implemented in Sprint 2');
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 shadow-xl p-6">
      <h2 className="text-xl font-semibold mb-4 text-white">Upload Protocol</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-white/80 text-sm font-medium mb-2" htmlFor="title">
            Protocol Title
          </label>
          <input
            id="title"
            type="text"
            className="w-full bg-white/10 border border-white/20 rounded-lg p-2 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-plasma-cyan focus:border-plasma-cyan"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-white/80 text-sm font-medium mb-2" htmlFor="author">
            Author
          </label>
          <input
            id="author"
            type="text"
            className="w-full bg-white/10 border border-white/20 rounded-lg p-2 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-plasma-cyan focus:border-plasma-cyan"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-white/80 text-sm font-medium mb-2" htmlFor="file">
            Protocol PDF
          </label>
          <input
            id="file"
            type="file"
            accept=".pdf"
            className="w-full bg-white/10 border border-white/20 rounded-lg p-2 text-white file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-plasma-cyan file:text-white hover:file:bg-electric-blue file:cursor-pointer"
            onChange={handleFileChange}
            required
          />
          {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>
        
        <button
          type="submit"
          disabled={uploading || !file || !title}
          className="bg-gradient-to-r from-plasma-cyan to-electric-blue hover:from-electric-blue hover:to-plasma-cyan text-white font-medium py-2 px-6 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload Protocol'}
        </button>
      </form>
      
      {success && (
        <div className="mt-4 p-3 bg-bio-emerald/20 text-bio-emerald border border-bio-emerald/30 rounded-lg backdrop-blur-sm">
          Protocol uploaded successfully!
        </div>
      )}
    </div>
  );
};

export default ProtocolUploader;