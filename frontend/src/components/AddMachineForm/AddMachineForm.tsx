// src/components/AddMachineForm/AddMachineForm.tsx
import React, { useState, useCallback } from 'react';
import { Check, Key, Lock, Upload, AlertCircle } from 'lucide-react';

interface AddMachineFormProps {
  onAdd: (data: {
    name: string;
    host: string;
    user: string;
    port: number;
    password?: string;
    ssh_key?: string;
  }) => Promise<void>;
}

export default function AddMachineForm({ onAdd }: AddMachineFormProps) {
  // Form state
  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("22");
  const [user, setUser] = useState("root");
  const [authType, setAuthType] = useState<'password' | 'sshkey'>('sshkey');
  const [password, setPassword] = useState("");
  const [sshKey, setSshKey] = useState("");
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  const validateSshKey = (key: string): boolean => {
    const trimmedKey = key.trim();
    return (
      trimmedKey.includes('BEGIN') &&
      trimmedKey.includes('PRIVATE KEY') &&
      trimmedKey.includes('END')
    );
  };

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setError("Name is required");
      return false;
    }
    if (!host.trim()) {
      setError("Host is required");
      return false;
    }
    if (!user.trim()) {
      setError("User is required");
      return false;
    }
    const portNum = parseInt(port);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      setError("Port must be a number between 1 and 65535");
      return false;
    }
    if (authType === 'password' && !password) {
      setError("Password is required when using password authentication");
      return false;
    }
    if (authType === 'sshkey' && !sshKey) {
      setError("SSH key is required when using key authentication");
      return false;
    }
    if (authType === 'sshkey' && sshKey && !validateSshKey(sshKey)) {
      setError("Invalid SSH key format. Must be a private key file.");
      return false;
    }
    return true;
  };

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsLoading(true);
      setError(null);
      setUploadedFileName(file.name);

      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          
          if (!validateSshKey(content)) {
            throw new Error('Invalid SSH key format. Must be a private key file.');
          }

          console.log('SSH key format validation:', {
            hasBegin: content.includes('BEGIN'),
            hasEnd: content.includes('END'),
            hasPrivateKey: content.includes('PRIVATE KEY'),
            lineCount: content.split('\n').length
          });

          setSshKey(content);
          setIsLoading(false);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to read SSH key');
          setSshKey('');
          setUploadedFileName(null);
          setIsLoading(false);
        }
      };

      reader.onerror = () => {
        setError('Failed to read file');
        setSshKey('');
        setUploadedFileName(null);
        setIsLoading(false);
      };

      reader.readAsText(file);
    }
  }, []);

  const clearForm = () => {
    setName("");
    setHost("");
    setPort("22");
    setUser("root");
    setPassword("");
    setSshKey("");
    setError(null);
    setUploadedFileName(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    try {
      const portNum = parseInt(port);
      const data = {
        name: name.trim(),
        host: host.trim(),
        user: user.trim(),
        port: portNum,
        ...(authType === 'password' ? { password } : {
          ssh_key: sshKey.trim().endsWith('\n') ? sshKey.trim() : sshKey.trim() + '\n'
        })
      };

      setIsLoading(true);
      await onAdd(data);
      clearForm();
    } catch (err) {
      console.error('Error in form submission:', err);
      setError(err instanceof Error ? err.message : 'Failed to add machine');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <h3 className="text-xl font-semibold mb-4">Add Machine</h3>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle className="text-red-500 mr-2 flex-shrink-0 mt-0.5" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Name:</label>
        <input 
          value={name} 
          onChange={e => setName(e.target.value)} 
          required 
          placeholder="e.g., Production Server 1"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Host:</label>
        <input 
          value={host} 
          onChange={e => setHost(e.target.value)} 
          required 
          placeholder="e.g., server.example.com or 192.168.1.100"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Port:</label>
        <input 
          type="number"
          value={port} 
          onChange={e => setPort(e.target.value)} 
          required 
          min="1"
          max="65535"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">User:</label>
        <input 
          value={user} 
          onChange={e => setUser(e.target.value)} 
          required 
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Authentication Method:</label>
        <div className="flex space-x-4 mb-4">
          <button
            type="button"
            onClick={() => {
              setAuthType('password');
              setSshKey('');
              setUploadedFileName(null);
              setError(null);
            }}
            className={`flex items-center px-4 py-2 rounded-md transition-colors ${
              authType === 'password' 
                ? 'bg-blue-100 text-blue-700 border-blue-300' 
                : 'bg-gray-100 text-gray-700 border-gray-300'
            } border`}
          >
            <Lock size={16} className="mr-2" />
            Password
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthType('sshkey');
              setPassword('');
              setError(null);
            }}
            className={`flex items-center px-4 py-2 rounded-md transition-colors ${
              authType === 'sshkey' 
                ? 'bg-blue-100 text-blue-700 border-blue-300' 
                : 'bg-gray-100 text-gray-700 border-gray-300'
            } border`}
          >
            <Key size={16} className="mr-2" />
            SSH Key
          </button>
        </div>

        {authType === 'password' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password:</label>
            <input 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              type="password" 
              required={authType === 'password'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SSH Private Key:</label>
              <div className="space-y-2">
                <textarea 
                  value={sshKey} 
                  onChange={e => {
                    setSshKey(e.target.value);
                    setUploadedFileName(null);
                  }}
                  required={authType === 'sshkey'}
                  rows={8}
                  placeholder="Paste your SSH private key here"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
                <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">- or -</span>
                  <div className="flex items-center space-x-2">
                    {uploadedFileName && (
                      <span className="text-sm text-gray-600">
                        {uploadedFileName}
                      </span>
                    )}
                    <label className={`flex items-center px-4 py-2 rounded-md cursor-pointer transition-colors ${
                      isLoading 
                        ? 'bg-gray-200 text-gray-500'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}>
                      <Upload size={16} className="mr-2" />
                      {isLoading ? 'Uploading...' : 'Upload Key File'}
                      <input
                        type="file"
                        onChange={handleFileUpload}
                        disabled={isLoading}
                        className="hidden"
                        accept=".key,.pem"
                      />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <button 
        type="submit" 
        className="w-full flex items-center justify-center bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        disabled={isLoading}
      >
        <Check size={16} className="mr-2" />
        {isLoading ? 'Processing...' : 'Add Machine'}
      </button>
    </form>
  );
}