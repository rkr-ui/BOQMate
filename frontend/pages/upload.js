import { useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../components/AuthContext';
import { useDropzone } from 'react-dropzone';
import { supabase } from '../utils/supabaseClient';
import CategorySelector from '../components/CategorySelector';

export default function Upload() {
  const { user } = useAuth();
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!user) {
      router.push('/login');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');
  }, [user, router, selectedCategories]);

    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session.access_token;

      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        // Add categories to form data if selected
        if (selectedCategories.length > 0) {
          formData.append('categories', selectedCategories.join(','));
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generate-boq`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          setSuccess(`Successfully processed ${file.name}. BOQ generated with ${result.length} items.`);
        } else {
          const errorData = await response.json();
          setError(`Failed to process ${file.name}: ${errorData.detail || 'Unknown error'}`);
        }
      }
    } catch (err) {
      setError('Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
    }
  }, [user, router]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/octet-stream': ['.dwg', '.dxf', '.rvt', '.rfa', '.dgn', '.skp'],
    },
    multiple: true,
  });

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Please log in to upload files.</p>
          <button
            onClick={() => router.push('/login')}
            className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Go to Login
          </button>
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
              <h1 className="text-xl font-semibold text-gray-900">BOQMate</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-indigo-600 hover:text-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
              >
                Dashboard
              </button>
              <span className="text-sm text-gray-700">Welcome, {user?.email}</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Upload Construction Documents
              </h2>
              <p className="text-gray-600">
                Upload your construction documents to generate AI-powered Bill of Quantities with 100% accuracy
              </p>
            </div>

            {/* Category Selector */}
            <CategorySelector onCategoriesChange={setSelectedCategories} />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
                {success}
              </div>
            )}

            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-indigo-400 bg-indigo-50'
                  : 'border-gray-300 hover:border-indigo-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="space-y-4">
                <div className="mx-auto h-12 w-12 text-gray-400">
                  <svg className="h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-900">
                    {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    or click to select files
                  </p>
                </div>
                <div className="text-xs text-gray-500">
                  Supported formats: PDF, TXT, DOCX, DWG, DXF, RVT, RFA, DGN, SKP
                </div>
              </div>
            </div>

            {uploading && (
              <div className="mt-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-600">Processing your file...</p>
              </div>
            )}

            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">How it works</h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-indigo-600">1</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">Upload your construction document</p>
                    <p className="text-sm text-gray-500">Support for PDF, CAD files, and text documents</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-indigo-600">2</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">AI processes your document with 100% accuracy</p>
                    <p className="text-sm text-gray-500">Our GPT-4o AI extracts precise quantities and current market rates</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-indigo-600">3</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">Download your BOQ</p>
                    <p className="text-sm text-gray-500">Get your Bill of Quantities in Excel or PDF format</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 