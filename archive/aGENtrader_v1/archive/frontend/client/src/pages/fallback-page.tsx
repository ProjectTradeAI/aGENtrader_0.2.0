
import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function FallbackPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [serverStatus, setServerStatus] = useState<'online'|'offline'>('offline');
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  
  useEffect(() => {
    async function checkServerStatus() {
      try {
        const response = await axios.get('/api/health');
        if (response.status === 200) {
          setServerStatus('online');
        }
      } catch (error) {
        setServerStatus('offline');
        if (error instanceof Error) {
          setErrorDetails(error.message);
        } else {
          setErrorDetails('Unknown error occurred');
        }
      } finally {
        setIsLoading(false);
      }
    }
    
    checkServerStatus();
  }, []);
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      padding: '20px',
      textAlign: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    }}>
      <h1 style={{fontSize: '28px', marginBottom: '16px'}}>Trading Bot Dashboard</h1>
      <div style={{
        background: '#f9f9f9',
        padding: '20px',
        borderRadius: '8px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{fontSize: '22px', marginBottom: '16px'}}>Application Status</h2>
        
        {isLoading ? (
          <div style={{color: '#666'}}>Checking server status...</div>
        ) : (
          <>
            {serverStatus === 'online' ? (
              <div style={{color: '#047857', marginBottom: '16px'}}>
                Server is online. Attempting to load application...
                <div style={{marginTop: '16px'}}>
                  <a 
                    href="/" 
                    style={{
                      backgroundColor: '#047857',
                      color: 'white',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      textDecoration: 'none',
                      fontWeight: 'bold'
                    }}
                  >
                    Reload Application
                  </a>
                </div>
              </div>
            ) : (
              <div style={{fontSize: '16px', marginBottom: '16px', color: '#e53e3e'}}>
                There was a problem loading the application
              </div>
            )}
            
            {errorDetails && (
              <div style={{
                padding: '12px',
                background: '#f5f5f5',
                border: '1px solid #ddd',
                borderRadius: '4px',
                textAlign: 'left',
                fontFamily: 'monospace',
                fontSize: '14px',
                overflowX: 'auto',
                marginBottom: '20px'
              }}>
                {errorDetails}
              </div>
            )}
          </>
        )}
        
        <div style={{marginTop: '24px', fontSize: '14px', color: '#666'}}>
          <div style={{fontWeight: 'bold', marginBottom: '8px'}}>Troubleshooting steps:</div>
          <ol style={{textAlign: 'left', paddingLeft: '20px'}}>
            <li>Check if the server is running</li>
            <li>Verify database connection</li>
            <li>Check console for any JavaScript errors</li>
            <li>Clear browser cache and reload</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
