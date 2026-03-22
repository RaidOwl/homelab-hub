<script>
  import { createEventDispatcher } from "svelte";

  export let values = [];
  export let placeholder = "";
  export let label = "";

  const dispatch = createEventDispatcher();

  function addValue() {
    values = [...values, ""];
    dispatch("change", values);
  }

  function removeValue(index) {
    values = values.filter((_, i) => i !== index);
    dispatch("change", values);
  }

  function updateValue(index, val) {
    values[index] = val;
    values = values;
    dispatch("change", values);
  }
</script>

<div class="multi-input">
  <div class="multi-input-header">
    <span class="multi-input-label">{label}</span>
    <button type="button" class="add-btn" on:click={addValue}>+ Add</button>
  </div>
  {#if values.length === 0}
    <button type="button" class="add-first-btn" on:click={addValue}>+ Add {label.toLowerCase()}</button>
  {:else}
    {#each values as value, index}
      <div class="multi-input-row">
        <input
          type="text"
          {placeholder}
          value={value}
          on:input={(e) => updateValue(index, e.target.value)}
        />
        <button type="button" class="remove-btn" on:click={() => removeValue(index)}>&times;</button>
      </div>
    {/each}
  {/if}
</div>

<style>
  .multi-input {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .multi-input-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .multi-input-label {
    font-size: 0.9rem;
    font-weight: 500;
  }
  .add-btn {
    padding: 0.15rem 0.5rem;
    font-size: 0.75rem;
    margin: 0;
    background: transparent;
    border: 1px solid #666;
    color: #ccc;
    border-radius: 4px;
    cursor: pointer;
  }
  .add-btn:hover {
    border-color: #999;
    color: #fff;
  }
  .add-first-btn {
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
    margin: 0;
    background: transparent;
    border: 1px dashed #555;
    color: #999;
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
    text-align: center;
  }
  .add-first-btn:hover {
    border-color: #888;
    color: #ccc;
  }
  .multi-input-row {
    display: flex;
    gap: 0.35rem;
    align-items: center;
  }
  .multi-input-row input {
    flex: 1;
    margin: 0;
  }
  .remove-btn {
    padding: 0.25rem 0.5rem;
    margin: 0;
    background: transparent;
    border: 1px solid rgba(220, 53, 69, 0.3);
    color: rgba(220, 53, 69, 0.8);
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    flex-shrink: 0;
  }
  .remove-btn:hover {
    background: rgba(220, 53, 69, 0.15);
    border-color: rgba(220, 53, 69, 0.5);
  }
</style>
