<script>
  import NetworkMap from "../components/map/NetworkMap.svelte";
  import TreeView from "../components/map/TreeView.svelte";
  import MapControls from "../components/map/MapControls.svelte";

  let mapComponent;
  let viewMode = "map"; // "map" or "tree"
</script>

<div class="map-page">
  <div class="map-header">
    <h2>Device Map</h2>
    <div class="header-controls">
      <div class="view-toggle">
        <button 
          class:active={viewMode === "map"} 
          on:click={() => viewMode = "map"}
        >
          Map View
        </button>
        <button 
          class:active={viewMode === "tree"} 
          on:click={() => viewMode = "tree"}
        >
          Tree View
        </button>
      </div>
      {#if viewMode === "map"}
        <MapControls 
          on:relayout={() => mapComponent?.relayout()} 
        />
      {/if}
    </div>
  </div>
  <div class="map-container">
    {#if viewMode === "map"}
      <NetworkMap bind:this={mapComponent} />
    {:else}
      <TreeView />
    {/if}
  </div>
</div>

<style>
  .map-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 3rem);
  }
  .map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  .map-header h2 {
    margin: 0;
  }
  .header-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .view-toggle {
    display: flex;
    gap: 0;
    border: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 6px;
    overflow: hidden;
  }
  .view-toggle button {
    margin: 0;
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    background: var(--pico-secondary-background, #2e2e3e);
    border: none;
    border-right: 1px solid var(--pico-muted-border-color, #333);
    color: #ffffff;
    cursor: pointer;
    border-radius: 0;
  }
  .view-toggle button:last-child {
    border-right: none;
  }
  .view-toggle button.active {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.2));
    color: var(--pico-primary, #6366f1);
  }
  .view-toggle button:hover:not(.active) {
    background: var(--pico-secondary-hover-background, #3e3e4e);
  }
  .map-container {
    flex: 1;
    border: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
  }
</style>
