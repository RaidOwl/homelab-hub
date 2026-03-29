<script>
  import { get, post } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";

  let importInput;

  async function exportDatabase() {
    try {
      const data = await get("/inventory/export");
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "homelab-export.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      addToast("Export downloaded", "success");
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      addToast(`Export failed: ${msg}`, "error");
    }
  }

  async function importDatabase(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      await post("/inventory/import", data);
      addToast("Import completed successfully!", "success");
      window.location.reload();
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      addToast(`Import failed: ${msg}`, "error");
    } finally {
      event.target.value = "";
    }
  }

  function triggerImport() {
    importInput?.click();
  }
</script>

<div class="settings-page">
  <h2>Settings</h2>

  <section class="card">
    <h3>Data backup</h3>
    <p class="muted">
      Export your inventory and docs as JSON, or restore from a previous export file.
    </p>
    <div class="actions">
      <button class="btn btn-primary" type="button" on:click={exportDatabase}>
        Export data
      </button>
      <button class="btn btn-secondary" type="button" on:click={triggerImport}>
        Import data
      </button>
      <input
        bind:this={importInput}
        type="file"
        accept=".json,application/json"
        class="sr-only"
        on:change={importDatabase}
      />
    </div>
  </section>
</div>

<style>
  .settings-page {
    max-width: 40rem;
  }
  .settings-page h2 {
    margin: 0 0 1.25rem;
  }
  .card {
    border: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    background: var(--pico-card-background-color, #1a1a2e);
  }
  .card h3 {
    margin: 0 0 0.5rem;
    font-size: 1.1rem;
  }
  .muted {
    margin: 0 0 1.25rem;
    color: var(--pico-muted-color, #aaa);
    font-size: 0.9rem;
    line-height: 1.5;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
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
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>
