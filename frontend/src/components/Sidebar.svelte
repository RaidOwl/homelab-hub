<script>
  import { location } from "svelte-spa-router";
  import { slide } from "svelte/transition";

  const inventoryTypes = [
    { key: "hardware", label: "Hardware" },
    { key: "vms", label: "VMs" },
    { key: "apps", label: "Apps" },
    { key: "storage", label: "Storage" },
    { key: "networks", label: "Networks" },
    { key: "misc", label: "Misc" },
  ];

  let inventoryExpanded = true;

  function isActive(itemPath, currentPath) {
    if (itemPath === "/") return currentPath === "/";
    return currentPath.startsWith(itemPath);
  }

  function isInventoryActive(currentPath) {
    return currentPath.startsWith("/inventory");
  }

  function toggleInventory() {
    inventoryExpanded = !inventoryExpanded;
  }
</script>

<nav class="sidebar open">
  <ul class="nav-list">
    <li class="section">
      <div
        class="section-header"
        class:active={isInventoryActive($location)}
        on:click={toggleInventory}
        on:keydown={(e) => e.key === 'Enter' && toggleInventory()}
        tabindex="0"
      >
        <span class="icon">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><g stroke-width="0"></g><g stroke-linecap="round" stroke-linejoin="round"></g><g><path d="m15.66 7-.91-2.68L8.62.85a1.28 1.28 0 0 0-1.24 0L1.25 4.32.34 7a1.24 1.24 0 0 0 .58 1.5l.33.18V11a1.25 1.25 0 0 0 .63 1l5.5 3.11a1.28 1.28 0 0 0 1.24 0l5.5-3.11a1.25 1.25 0 0 0 .63-1V8.68l.33-.18a1.24 1.24 0 0 0 .58-1.5zM10 9.87l-.48-1.28L14 6.13l.44 1.28zM8 1.94 13.46 5 8 8 2.54 5zM1.52 7.41 2 6.13l4.48 2.46L6 9.87zm1 1.95 4.25 2.32.62-1.84v3.87L2.5 11zM13.5 11l-4.88 2.71V9.84l.63 1.84 4.25-2.32z"></path></g></svg>
        </span>
        <span class="section-title">Inventory</span>
        <span class="expand-icon">
          {#if inventoryExpanded}
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          {:else}
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          {/if}
        </span>
      </div>
      {#if inventoryExpanded}
        <ul class="subsection" transition:slide={{ duration: 200 }}>
          {#each inventoryTypes as type}
            <li>
              <a
                href={"#/inventory/" + type.key}
                class:active={$location === "/inventory/" + type.key}
              >
                {type.label}
              </a>
            </li>
          {/each}
        </ul>
      {/if}
    </li>
    <li>
      <a
        href="#/map"
        class:active={isActive("/map", $location)}
      >
        <span class="icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="7" y1="8" x2="11" y2="16"/><line x1="17" y1="8" x2="13" y2="16"/></svg></span>
        Map
      </a>
    </li>
    <li>
      <a
        href="#/docs"
        class:active={isActive("/docs", $location)}
      >
        <span class="icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg></span>
        Docs
      </a>
    </li>
  </ul>
</nav>

<style>
  .sidebar {
    width: 0;
    background: var(--pico-card-background-color, #1a1a2e);
    border-right: 1px solid var(--pico-muted-border-color, #333);
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow-y: auto;
    flex-shrink: 0;
    height: 100vh;
    position: sticky;
    top: 0;
    transition: width 0.3s;
  }

  .sidebar.open {
    width: 220px;
  }

  .nav-list {
    list-style: none;
    padding: 0.5rem 0;
    margin: 0;
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }
  .nav-list > li {
    display: block;
    width: 100%;
    padding-left: 0;
  }
  .sidebar li a {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    text-decoration: none;
    color: var(--pico-muted-color, #aaa);
    border-radius: 0;
    transition: background 0.15s;
    width: 100%;
    box-sizing: border-box;
  }
  .sidebar li a:hover {
    background: transparent;
  }
  .sidebar li a.active {
    color: var(--pico-primary, #6366f1);
    font-weight: 600;
  }
  .icon {
    font-size: 1.1rem;
    width: 1.5rem;
    text-align: center;
    flex-shrink: 0;
  }
  .section {
    margin: 0;
    display: block;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    color: var(--pico-muted-color, #aaa);
    font-weight: 500;
    cursor: pointer;
    width: 100%;
    box-sizing: border-box;
    transition: background 0.15s;
    background: transparent;
    border: none;
    border-radius: 0;
    text-decoration: none;
  }
  :global(nav.sidebar),
  :global(nav.sidebar ul) {
    padding: 0;
    margin: 0;
  }
  :global(nav.sidebar .section-header) {
    color: var(--pico-muted-color, #aaa) !important;
    padding-left: 1rem;
  }
  :global(nav.sidebar .section-header.active) {
    color: var(--pico-primary, #6366f1) !important;
  }
  .section-header:hover {
    background: transparent;
  }
  .section-header:focus,
  .section-header:focus-visible {
    outline: none;
    background: transparent;
  }
  .section-header.active {
    color: var(--pico-primary, #6366f1);
    background: transparent !important;
  }
  .section-title {
    flex: 1;
    text-align: left;
  }
  .expand-icon {
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }
  .subsection {
    padding: 0;
    margin: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
  }
  .subsection li {
    margin: 0;
    display: block;
    width: 100%;
  }
  .subsection a {
    padding: 0.5rem 1rem 0.5rem 2.5rem;
    font-size: 0.9rem;
    display: flex;
    width: 100%;
    box-sizing: border-box;
  }
</style>
