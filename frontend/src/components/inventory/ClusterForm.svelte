<script>
  import IconPicker from "./IconPicker.svelte";

  export let item = {};
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>Description<input type="text" bind:value={item.description} /></label>
</div>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
