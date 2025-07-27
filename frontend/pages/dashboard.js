import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../components/AuthContext';
import { supabase } from '../utils/supabaseClient';

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    fetchUserFiles();
  }, [user]);

  const fetchUserFiles = async () => {
    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session.access_token;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFiles(data);
      } else {
        setError('Failed to fetch files');
      }
    } catch (err) {
      setError('Failed to fetch files');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  const downloadFile = async (fileId) => {
    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session.access_token;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files/${fileId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = files.find(f => f.id === fileId)?.filename || 'download';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to download file');
    }
  };

  const downloadBOQ = async (fileId) => {
    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session.access_token;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files/${fileId}/boq`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${files.find(f => f.id === fileId)?.filename}_BOQ.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to download BOQ');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">BOQMate Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user?.email}</span>
              <button
                onClick={handleSignOut}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Files</h2>
            <button
              onClick={() => router.push('/upload')}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Upload New File
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {files.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No files uploaded yet.</p>
              <button
                onClick={() => router.push('/upload')}
                className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Upload Your First File
              </button>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {files.map((file) => (
                  <li key={file.id} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            <svg className="h-6 w-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{file.filename}</div>
                          <div className="text-sm text-gray-500">
                            Uploaded on {new Date(file.uploaded_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => downloadFile(file.id)}
                          className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Download File
                        </button>
                        {file.boq_data && (
                          <button
                            onClick={() => downloadBOQ(file.id)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Download BOQ
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 