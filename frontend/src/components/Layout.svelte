<script>
  import { isMobile } from "../lib/stores";
  import Sidebar from "./Sidebar.svelte";
  import { onMount } from 'svelte';

  // In production (Docker), use relative URLs. In dev, use explicit URL for proxy.
  const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:5001');

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

  let lastMobile = null;
  function handleResize() {
    const mobile = window.innerWidth <= 768;
    if (mobile === lastMobile) return;
    lastMobile = mobile;
    isMobile.set(mobile);

    const sidebar = document.querySelector('nav.sidebar');
    if (sidebar) {
      if (mobile) sidebar.classList.remove('open');
      else sidebar.classList.add('open');
    }
  }

  onMount(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });

  function toggleNav() {
    document.querySelector('nav.sidebar')?.classList.toggle('open');
  }
</script>

<div class="layout">
  <header class="header">
    <div class="header-title">
      <button class="nav-toggle" on:click={toggleNav}>
        <span class="icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
      </button>
      <h1>Home Lab Hub</h1>
    </div>
    <div class="header-actions">
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

  .header-title {
    display: flex;
    flex-direction: row;
    gap: 1rem;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .nav-toggle {
    all: unset;
    cursor: pointer;
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
