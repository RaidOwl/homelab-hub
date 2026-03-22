<script>
  import IconPicker from "./IconPicker.svelte";
  import MultiInput from "./MultiInput.svelte";

  export let item = {};

  let ipAddresses = item.ip_address ? item.ip_address.split(",").map(s => s.trim()).filter(Boolean) : [];

  function handleIpChange(e) {
    ipAddresses = e.detail;
    item.ip_address = ipAddresses.filter(Boolean).join(", ") || null;
  }
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>Category<input type="text" bind:value={item.category} /></label>
</div>
<div class="grid">
  <label>Hostname<input type="text" bind:value={item.hostname} /></label>
  <MultiInput
    label="IP Addresses"
    placeholder="e.g. 192.168.1.10"
    values={ipAddresses}
    on:change={handleIpChange}
  />
</div>
<label>Description<textarea bind:value={item.description} rows="2"></textarea></label>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
