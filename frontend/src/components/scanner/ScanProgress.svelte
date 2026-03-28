<script>
  /** @type {string} */
  export let status = "idle";
  /** @type {number} */
  export let progress = 0;
  /** @type {string | null} */
  export let error = null;
  /** @type {string} */
  export let label = "Scanning…";
</script>

<div class="scan-progress" role="status" aria-live="polite">
  {#if error}
    <p class="error">{error}</p>
  {:else if status === "running"}
    <p class="label">{label}</p>
    <progress value={progress} max="100"></progress>
    <span class="pct">{progress}%</span>
  {:else if status === "completed"}
    <p class="done">Done.</p>
  {:else if status === "failed"}
    <p class="error">Scan failed.</p>
  {:else}
    <p class="idle">Ready.</p>
  {/if}
</div>

<style>
  .scan-progress {
    margin: 0.75rem 0;
    max-width: 420px;
  }
  .label {
    margin: 0 0 0.35rem;
    font-size: 0.9rem;
    color: var(--pico-muted-color, #aaa);
  }
  progress {
    width: 100%;
    height: 0.5rem;
  }
  .pct {
    font-size: 0.8rem;
    color: var(--pico-muted-color, #888);
  }
  .done {
    margin: 0;
    color: var(--pico-ins-color, #2ecc71);
  }
  .idle {
    margin: 0;
    color: var(--pico-muted-color, #666);
  }
  .error {
    margin: 0;
    color: var(--pico-del-color, #e74c3c);
  }
</style>
