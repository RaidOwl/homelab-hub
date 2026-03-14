<script>
  import { createEventDispatcher } from "svelte";
  import { isAdmin } from "../../lib/stores.js";

  const dispatch = createEventDispatcher();

  export let maxChildrenPerLevel = 8;
</script>

<div class="map-controls">
  <label class="config-label">
    Max children/row:
    <input
      type="number"
      min="1"
      max="50"
      class="config-input"
      bind:value={maxChildrenPerLevel}
      on:change={() => dispatch("relayout")}
    />
  </label>
  {#if $isAdmin}
    <button class="outline small" on:click={() => dispatch("relayout")}>Auto Layout</button>
  {/if}
</div>

<style>
  .map-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .small {
    padding: 0.3rem 0.75rem;
    font-size: 0.85rem;
    margin: 0;
  }
  .config-label {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  .config-input {
    width: 3.5rem;
    padding: 0.2rem 0.4rem;
    font-size: 0.85rem;
    margin: 0;
  }
</style>
