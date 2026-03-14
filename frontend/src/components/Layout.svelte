<script>
  import Sidebar from "./Sidebar.svelte";
  import { authToken, isAdmin, addToast } from "../lib/stores.js";
  import { get as getStore } from "svelte/store";

  // In production (Docker), use relative URLs. In dev, use explicit URL for proxy.
  const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:5001');

  let showLoginModal = false;
  let loginPassword = "";
  let loginError = "";
  let loginLoading = false;

  function openLogin() {
    loginPassword = "";
    loginError = "";
    showLoginModal = true;
  }

  function closeLogin() {
    showLoginModal = false;
  }

  async function handleLogin() {
    loginLoading = true;
    loginError = "";
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: loginPassword }),
      });
      const data = await res.json();
      if (res.ok) {
        authToken.set(data.token);
        showLoginModal = false;
        addToast("Logged in as admin", "success");
      } else {
        loginError = data.error || "Login failed";
      }
    } catch (e) {
      loginError = "Login failed";
    }
    loginLoading = false;
  }

  async function handleLogout() {
    const token = getStore(authToken);
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
    }).catch(() => {});
    authToken.set(null);
    addToast("Logged out", "info");
  }

  async function exportDatabase() {
    try {
      const token = getStore(authToken);
      const headers = { 'Accept': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const response = await fetch(`${API_BASE}/inventory/export`, {
        method: 'GET',
        headers,
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
          'Authorization': `Bearer ${getStore(authToken)}`,
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
      <button class="btn btn-primary" on:click={exportDatabase}>Export Data</button>
      {#if $isAdmin}
        <button class="btn btn-secondary" on:click={triggerImport}>Import Data</button>
        <input id="import-file-input" type="file" accept=".json" style="display: none;" on:change={importDatabase} />
        <span class="admin-badge">Admin</span>
        <button class="btn btn-outline" on:click={handleLogout}>Logout</button>
      {:else}
        <button class="btn btn-outline" on:click={openLogin}>Login</button>
      {/if}
    </div>
  </header>
  
  <div class="content">
    <Sidebar />
    <main class="main">
      <slot />
    </main>
  </div>
</div>

{#if showLoginModal}
  <div class="modal-overlay" on:click|self={closeLogin} role="dialog" aria-modal="true" aria-label="Admin Login">
    <div class="modal-box">
      <h2>Admin Login</h2>
      <form on:submit|preventDefault={handleLogin}>
        <label>
          Password
          <input
            type="password"
            bind:value={loginPassword}
            placeholder="Enter admin password"
            autofocus
          />
        </label>
        {#if loginError}
          <p class="login-error">{loginError}</p>
        {/if}
        <div class="modal-actions">
          <button type="submit" class="btn btn-primary" disabled={loginLoading}>
            {loginLoading ? "Logging in..." : "Login"}
          </button>
          <button type="button" class="btn btn-secondary" on:click={closeLogin}>Cancel</button>
        </div>
      </form>
    </div>
  </div>
{/if}

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

  .btn-outline {
    background-color: transparent;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.5);
  }

  .btn-outline:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  .admin-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.6rem;
    background-color: #28a745;
    color: white;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-box {
    background: #1a1d23;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 2rem;
    width: 100%;
    max-width: 380px;
  }

  .modal-box h2 {
    margin: 0 0 1.5rem;
    font-size: 1.25rem;
    color: white;
  }

  .login-error {
    color: #e74c3c;
    font-size: 0.875rem;
    margin: 0.5rem 0;
  }

  .modal-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
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
