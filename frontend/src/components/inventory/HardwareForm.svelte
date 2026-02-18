<script>
  import IconPicker from "./IconPicker.svelte";

  export let item = {};
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>Hostname<input type="text" bind:value={item.hostname} /></label>
</div>
<div class="grid">
  <label>IP Address<input type="text" bind:value={item.ip_address} /></label>
  <label>MAC Address<input type="text" bind:value={item.mac_address} placeholder="00:00:00:00:00:00" /></label>
</div>
<div class="grid">
  <label>OS<input type="text" bind:value={item.os} /></label>
</div>
<div class="grid">
  <label>CPU<input type="text" bind:value={item.cpu} /></label>
  <label>CPU Cores<input type="number" bind:value={item.cpu_cores} /></label>
  <label>RAM (GB)<input type="number" step="0.1" bind:value={item.ram_gb} /></label>
</div>
<div class="grid">
  <label>Make<input type="text" bind:value={item.make} /></label>
  <label>Model<input type="text" bind:value={item.model} /></label>
</div>
<div class="grid">
  <label>Serial Number<input type="text" bind:value={item.serial_number} /></label>
  <label>Location<input type="text" bind:value={item.location} /></label>
</div>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
