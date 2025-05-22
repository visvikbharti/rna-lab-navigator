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
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Upload Protocol</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="title">
            Protocol Title
          </label>
          <input
            id="title"
            type="text"
            className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="author">
            Author
          </label>
          <input
            id="author"
            type="text"
            className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="file">
            Protocol PDF
          </label>
          <input
            id="file"
            type="file"
            accept=".pdf"
            className="w-full border rounded-lg p-2 text-gray-700"
            onChange={handleFileChange}
            required
          />
          {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>
        
        <button
          type="submit"
          disabled={uploading || !file || !title}
          className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition duration-150 ease-in-out disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload Protocol'}
        </button>
      </form>
      
      {success && (
        <div className="mt-4 p-3 bg-green-100 text-green-800 rounded-lg">
          Protocol uploaded successfully!
        </div>
      )}
    </div>
  );
};

export default ProtocolUploader;