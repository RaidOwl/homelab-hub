<script>
  /**
   * @typedef {{ key: string, label: string }} Col
   * @type {Col[]}
   */
  export let columns = [];
  /** @type {Record<string, unknown>[]} */
  export let rows = [];
  /**
   * @type {(row: Record<string, unknown>, index: number) => string}
   */
  export let rowId = (row, index) => String(index);
  /** @type {string[]} */
  export let selectedIds = [];
  /** @type {(row: Record<string, unknown>, index: number) => string | null} */
  export let rowBadge = () => null;

  let sortColumn = null;
  let sortDirection = "asc";

  function toggleSort(col) {
    if (sortColumn === col) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      sortColumn = col;
      sortDirection = "asc";
    }
  }

  $: sorted =
    sortColumn && rows.length
      ? [...rows].sort((a, b) => {
          let av = a[sortColumn];
          let bv = b[sortColumn];
          if (av == null) av = "";
          if (bv == null) bv = "";
          if (typeof av === "number" && typeof bv === "number") {
            return sortDirection === "asc" ? av - bv : bv - av;
          }
          const as = String(av).toLowerCase();
          const bs = String(bv).toLowerCase();
          if (as < bs) return sortDirection === "asc" ? -1 : 1;
          if (as > bs) return sortDirection === "asc" ? 1 : -1;
          return 0;
        })
      : rows;

  function isSelected(id) {
    return selectedIds.includes(id);
  }

  function toggleRow(id, checked) {
    if (checked) {
      selectedIds = [...selectedIds, id];
    } else {
      selectedIds = selectedIds.filter((x) => x !== id);
    }
  }

  function toggleAll(checked) {
    if (checked) {
      selectedIds = sorted.map((r, i) => rowId(r, i));
    } else {
      selectedIds = [];
    }
  }

  $: allIds = sorted.map((r, i) => rowId(r, i));
  $: allSelected =
    allIds.length > 0 && allIds.every((id) => selectedIds.includes(id));
</script>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th class="chk">
          <input
            type="checkbox"
            checked={allSelected}
            on:change={(e) => toggleAll(e.currentTarget.checked)}
            aria-label="Select all"
          />
        </th>
        {#each columns as col}
          <th class="sortable" on:click={() => toggleSort(col.key)}>
            {col.label}
            {#if sortColumn === col.key}
              <span class="ind">{sortDirection === "asc" ? "▲" : "▼"}</span>
            {/if}
          </th>
        {/each}
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each sorted as row, index (rowId(row, index))}
        {@const id = rowId(row, index)}
        {@const badge = rowBadge(row, index)}
        <tr>
          <td class="chk">
            <input
              type="checkbox"
              checked={isSelected(id)}
              on:change={(e) => toggleRow(id, e.currentTarget.checked)}
            />
          </td>
          {#each columns as col}
            <td>{row[col.key] ?? ""}</td>
          {/each}
          <td>
            {#if badge}
              <span class="badge">{badge}</span>
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .table-wrap {
    overflow-x: auto;
    margin-top: 0.5rem;
  }
  th.sortable {
    cursor: pointer;
    user-select: none;
  }
  th.sortable:hover {
    background: rgba(255, 255, 255, 0.04);
  }
  .ind {
    font-size: 0.65rem;
    margin-left: 0.25rem;
    opacity: 0.7;
  }
  th.chk,
  td.chk {
    width: 2.5rem;
    text-align: center;
  }
  .badge {
    font-size: 0.75rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    background: rgba(250, 204, 21, 0.15);
    color: #fbbf24;
    white-space: nowrap;
  }
</style>
