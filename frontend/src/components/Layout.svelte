<script>
  import { onMount } from "svelte";
  import Sidebar from "./Sidebar.svelte";

  // In production (Docker), use relative URLs. In dev, use explicit URL for proxy.
  const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:5001');

  let authUser = null;

  onMount(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/user`);
      if (res.ok) {
        const data = await res.json();
        if (data.username) authUser = data;
      }
    } catch (e) {
      // Auth not available — ignore
    }
  });

  async function exportDatabase() {
    try {
      const response = await fetch(`${API_BASE}/inventory/export`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Create a blob and download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'homelab-export.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed: ' + error.message);
    }
  }

  async function importDatabase(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      const response = await fetch(`${API_BASE}/inventory/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      alert('Import completed successfully!');
      window.location.reload();
    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed: ' + error.message);
    }
  }

  function triggerImport() {
    document.getElementById('import-file-input').click();
  }
</script>

<div class="layout">
  <header class="header">
    <h1>Home Lab Hub</h1>
    <div class="header-actions">
      {#if authUser}
        <span class="auth-user">{authUser.name || authUser.username}</span>
      {/if}
      <button class="btn btn-primary" on:click={exportDatabase}>Export Data</button>
      <button class="btn btn-secondary" on:click={triggerImport}>Import Data</button>
      <input id="import-file-input" type="file" accept=".json" style="display: none;" on:change={importDatabase} />
    </div>
  </header>
  
  <div class="content">
    <Sidebar />
    <main class="main">
      <slot />
    </main>
  </div>
</div>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  
  .header {
    background-color: #1a1d23;
    color: white;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .header h1 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .header-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .auth-user {
    color: #aaa;
    font-size: 0.9rem;
    margin-right: 0.5rem;
  }
  
  .btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    line-height: 1.5;
    text-align: center;
    vertical-align: middle;
    box-sizing: border-box;
  }
  
  .btn-primary {
    background-color: #007bff;
    color: white;
  }
  
  .btn-primary:hover {
    background-color: #0056b3;
  }
  
  .btn-secondary {
    background-color: #6c757d;
    color: white;
  }
  
  .btn-secondary:hover {
    background-color: #545b62;
  }
  
  .content {
    display: flex;
    flex: 1;
  }
  
  .main {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
  }
</style>
