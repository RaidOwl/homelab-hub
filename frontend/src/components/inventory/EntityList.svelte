<script>
  import { push } from "svelte-spa-router";
  import { get, post, del } from "../../lib/api.js";
  import { addToast, isMobile } from "../../lib/stores.js";
  import Modal from "../Modal.svelte";
  import HardwareForm from "./HardwareForm.svelte";
  import VmForm from "./VmForm.svelte";
  import AppForm from "./AppForm.svelte";
  import StorageForm from "./StorageForm.svelte";
  import NetworkForm from "./NetworkForm.svelte";
  import MiscForm from "./MiscForm.svelte";

  export let type = "hardware";

  let items = [];
  let loading = true;
  let search = "";
  let showCreateModal = false;
  let newItem = {};
  let sortColumn = null;
  let sortDirection = 'asc';

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
    apps: AppForm,
    storage: StorageForm,
    networks: NetworkForm,
    misc: MiscForm,
  };

  const COLUMNS = {
    hardware: ["name", "hostname", "ip_address", "os", "cpu", "ram_gb"],
    vms: ["name", "hostname", "ip_address", "os", "cpu_cores", "ram_gb"],
    apps: ["name", "hostname", "ip_address", "external_hostname", "port"],
    storage: ["name", "storage_type", "raid_type", "raw_space_tb", "usable_space_tb"],
    networks: ["name", "vlan_id", "subnet", "gateway"],
    misc: ["name", "category", "hostname", "ip_address"],
  };

  const LABELS = {
    ip_address: "IP Address",
    ram_gb: "RAM (GB)",
    cpu_cores: "CPU Cores",
    external_hostname: "External Host",
    vlan_id: "VLAN ID",
    raw_space_tb: "Raw (TB)",
    usable_space_tb: "Usable (TB)",
    storage_type: "Type",
    raid_type: "RAID",
  };

  function label(col) {
    return LABELS[col] || col.charAt(0).toUpperCase() + col.slice(1).replace(/_/g, " ");
  }

  $: columns = COLUMNS[type] || ["name"];
  $: FormComponent = FORMS[type];
  $: modalTitle = `Add ${type.charAt(0).toUpperCase() + type.slice(1).replace(/s$/, "")}`;

  async function loadItems() {
    loading = true;
    items = []; // Clear items before loading
    try {
      const res = await get(`/${type}`);
      items = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
    loading = false;
  }

  // Reload whenever type changes
  $: type, loadItems();

  $: filtered = search
    ? items.filter((item) =>
        Object.values(item).some(
          (v) => v && String(v).toLowerCase().includes(search.toLowerCase())
        )
      )
    : items;

  function sortBy(column) {
    if (sortColumn === column) {
      // Toggle direction if clicking same column
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      // New column, default to ascending
      sortColumn = column;
      sortDirection = 'asc';
    }
  }

  $: sorted = sortColumn
    ? [...filtered].sort((a, b) => {
        let aVal = a[sortColumn];
        let bVal = b[sortColumn];

        // Handle null/undefined values
        if (aVal == null) aVal = '';
        if (bVal == null) bVal = '';

        // Convert to strings for comparison if not numbers
        if (typeof aVal === 'string') aVal = aVal.toLowerCase();
        if (typeof bVal === 'string') bVal = bVal.toLowerCase();

        // Compare
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      })
    : filtered;

  async function deleteItem(id) {
    if (!confirm("Delete this item?")) return;
    try {
      await del(`/${type}/${id}`);
      addToast("Deleted", "success");
      loadItems();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function duplicateItem(item) {
    try {
      // Create a copy of the item
      const duplicate = { ...item };
      // Remove id and update name
      delete duplicate.id;
      duplicate.name = `Copy of ${item.name}`;

      // Create the duplicate
      await post(`/${type}`, duplicate);
      addToast("Duplicated successfully", "success");
      loadItems();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  function handleAddClick() {
    newItem = {};
    showCreateModal = true;
  }

  function handleModalClose() {
    showCreateModal = false;
    newItem = {};
  }

  async function handleCreate() {
    try {
      await post(`/${type}`, newItem);
      addToast("Created successfully", "success");
      showCreateModal = false;
      newItem = {};
      loadItems();
    } catch (e) {
      addToast(e.message, "error");
    }
  }
  
  function handleCardViewToggle() {
    this.classList.toggle('outline');
    const tableWrap = document.querySelector('.table-wrap');
    const classAction = !this.classList.contains('outline') ? 'add' : 'remove';
    tableWrap.classList[classAction]('card-view');
  }
</script>

<div class="entity-list">
  <div class="list-header">
    <h2>{type.charAt(0).toUpperCase() + type.slice(1)}</h2>
    <div class="actions">
      <input type="search" placeholder="Filter..." bind:value={search} />
      <button on:click={handleAddClick}>+ Add</button>
      <button class="table-toggle" on:click={handleCardViewToggle}>Card View</button>
    </div>
  </div>

  {#if loading}
    <p aria-busy="true">Loading...</p>
  {:else if filtered.length === 0}
    <p>No items found.</p>
  {:else}
    <div class="table-wrap card-view">
      {#if $isMobile}
        <div class="mobile-sort">
          <select bind:value={sortColumn}>
            <option value={null} disabled selected>Sort by...</option>
            {#each columns as col}
              <option value={col}>
                {label(col)}
              </option>
            {/each}
          </select>

          <button
            class="sort-direction"
            on:click={() => sortBy(sortColumn)}
            disabled={sortColumn === null}
          >
            {sortDirection === 'asc' ? '▲' : '▼'}
          </button>
        </div>
      {/if}
      <table>
        <thead>
          <tr>
            {#each columns as col}
              <th class="sortable" on:click={() => sortBy(col)}>
                {label(col)}
                {#if sortColumn === col}
                  <span class="sort-indicator">{sortDirection === 'asc' ? '▲' : '▼'}</span>
                {/if}
              </th>
            {/each}
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each sorted as item (item.id)}
            <tr on:click={() => push(`/inventory/${type}/${item.id}`)} class="clickable">
              {#each columns as col}
                <td data-label={label(col)}>{item[col] || "-"}</td>
              {/each}
              <td>
                <div class="button-group">
                  <button class="outline secondary small" on:click|stopPropagation={() => duplicateItem(item)}>
                    Duplicate
                  </button>
                  <button class="outline secondary small btn-delete" on:click|stopPropagation={() => deleteItem(item.id)}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<Modal
  isOpen={showCreateModal}
  title={modalTitle}
  maxWidth="700px"
  on:close={handleModalClose}
>
  <form on:submit|preventDefault={handleCreate}>
    <svelte:component this={FormComponent} bind:item={newItem} />

    <div class="form-actions">
      <button type="submit" class="btn-primary">Create</button>
      <button type="button" class="btn-secondary" on:click={handleModalClose}>Cancel</button>
    </div>
  </form>
</Modal>

<style>
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  .list-header h2 {
    margin: 0;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .actions input {
    margin: 0;
    flex: 1;
  }
  .actions button {
    margin: 0;
    white-space: nowrap;
  }
  .table-wrap {
    overflow-x: auto;
  }
  th.sortable {
    cursor: pointer;
    user-select: none;
    position: relative;
    padding-right: 1.5rem;
  }
  th.sortable:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  .sort-indicator {
    position: absolute;
    right: 0.5rem;
    font-size: 0.7rem;
    opacity: 0.7;
  }
  tbody tr {
    min-width: 300px;
  }
  tr.clickable {
    cursor: pointer;
  }
  tr.clickable:hover {
    background: var(--pico-primary-hover-background, rgba(255, 255, 255, 0.03));
  }
  .small {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
  }
  .button-group {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }

  form {
    display: flex;
    flex-direction: column;
  }

  .form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid #444;
  }

  .btn-primary {
    padding: 0.5rem 1rem;
    background: #4a9eff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .btn-primary:hover {
    background: #3a8eef;
  }

  .btn-secondary {
    padding: 0.5rem 1rem;
    background: #444;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .btn-secondary:hover {
    background: #555;
  }

  .btn-delete {
    background: rgba(220, 53, 69, 0.15) !important;
    border-color: rgba(220, 53, 69, 0.3) !important;
  }

  .btn-delete:hover {
    background: rgba(220, 53, 69, 0.25) !important;
    border-color: rgba(220, 53, 69, 0.5) !important;
  }
  
  .table-toggle, .mobile-sort { display: none; }

  .card-view .mobile-sort {
    display: flex;
    gap: 1rem;
  }

  .card-view .sort-direction {
    margin: 0;
    white-space: nowrap;
    margin-bottom: var(--pico-spacing);
  }

  @media (max-width: 768px) {
    .list-header {
      gap: 1.5rem;
    }
    .list-header h2 {
      flex: 1;
      text-align: center;
    }
    
    .table-toggle { display: block; }
    .card-view table,
    .card-view tbody,
    .card-view th,
    .card-view td,
    .card-view tr { display: block; }
    .card-view thead { display: none; }
    .card-view tr {
      margin-bottom: 1em;
      border: 3px solid var(--pico-table-border-color);
      border-radius: 0.5em;
    }
    .card-view td {
      position: relative;
      padding-left: 50%;
      border: none;
      border-bottom: var(--pico-border-width) solid var(--pico-table-border-color);
    }
    .card-view td:last-child {
      border-bottom: none;
    }
    .card-view td::before {
      content: attr(data-label);
      position: absolute;
      left: 0;
      width: 45%;
      padding-left: 0.5em;
      font-weight: bold;
    }
  }
</style>
