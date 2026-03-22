<script>
  import IconPicker from "./IconPicker.svelte";
  import MultiInput from "./MultiInput.svelte";

  export let item = {};

  // Parse comma-separated strings into arrays for editing
  let ipAddresses = item.ip_address ? item.ip_address.split(",").map(s => s.trim()).filter(Boolean) : [];
  let macAddresses = item.mac_address ? item.mac_address.split(",").map(s => s.trim()).filter(Boolean) : [];

  function handleIpChange(e) {
    ipAddresses = e.detail;
    item.ip_address = ipAddresses.filter(Boolean).join(", ") || null;
  }

  function handleMacChange(e) {
    macAddresses = e.detail;
    item.mac_address = macAddresses.filter(Boolean).join(", ") || null;
  }
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>Hostname<input type="text" bind:value={item.hostname} /></label>
</div>
<div class="grid">
  <MultiInput
    label="IP Addresses"
    placeholder="e.g. 192.168.1.10"
    values={ipAddresses}
    on:change={handleIpChange}
  />
  <MultiInput
    label="MAC Addresses"
    placeholder="00:00:00:00:00:00"
    values={macAddresses}
    on:change={handleMacChange}
  />
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
