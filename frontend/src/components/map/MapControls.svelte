<script>
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();
</script>

<div class="map-controls">
  <button class="outline small" on:click={() => dispatch("relayout")}>
    Auto Layout
  </button>
</div>

<style>
  .map-controls {
    display: flex;
    gap: 0.5rem;
  }
  .small {
    padding: 0.3rem 0.75rem;
    font-size: 0.85rem;
    margin: 0;
  }
</style>
