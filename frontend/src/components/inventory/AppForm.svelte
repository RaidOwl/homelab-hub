<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";
  import MultiInput from "./MultiInput.svelte";

  export let item = {};

  let hardwareOptions = [];
  let vmOptions = [];
  let parentType = item.vm_id ? "vm" : item.hardware_id ? "hardware" : "none";
  let previousHardwareId = item.hardware_id;
  let previousVmId = item.vm_id;

  let ipAddresses = item.ip_address ? item.ip_address.split(",").map(s => s.trim()).filter(Boolean) : [];

  function handleIpChange(e) {
    ipAddresses = e.detail;
    item.ip_address = ipAddresses.filter(Boolean).join(", ") || null;
  }

  onMount(async () => {
    try {
      const [hwRes, vmRes] = await Promise.all([get("/hardware"), get("/vms")]);
      hardwareOptions = hwRes.data;
      vmOptions = vmRes.data;
    } catch (e) {
      // ignore
    }
    if (item.vm_id) parentType = "vm";
    else if (item.hardware_id) parentType = "hardware";
  });

  $: {
    if (parentType === "none") {
      item.hardware_id = null;
      item.vm_id = null;
    } else if (parentType === "hardware") {
      item.vm_id = null;
    } else if (parentType === "vm") {
      item.hardware_id = null;
    }
  }

  // Auto-populate hostname and first IP from parent only when creating a new app
  $: if (!item.id && item.hardware_id && hardwareOptions.length > 0 && item.hardware_id !== previousHardwareId) {
    const hardware = hardwareOptions.find(h => h.id === item.hardware_id);
    if (hardware) {
      if (hardware.hostname && !item.hostname) {
        item.hostname = hardware.hostname;
      }
      if (hardware.ip_address && ipAddresses.length === 0) {
        // Take the first IP from the parent
        const firstIp = hardware.ip_address.split(",")[0].trim();
        ipAddresses = [firstIp];
        item.ip_address = firstIp;
      }
    }
    previousHardwareId = item.hardware_id;
  }

  $: if (!item.id && item.vm_id && vmOptions.length > 0 && item.vm_id !== previousVmId) {
    const vm = vmOptions.find(v => v.id === item.vm_id);
    if (vm) {
      if (vm.hostname && !item.hostname) {
        item.hostname = vm.hostname;
      }
      if (vm.ip_address && ipAddresses.length === 0) {
        const firstIp = vm.ip_address.split(",")[0].trim();
        ipAddresses = [firstIp];
        item.ip_address = firstIp;
      }
    }
    previousVmId = item.vm_id;
  }
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>
    Runs on
    <select bind:value={parentType}>
      <option value="none">Standalone</option>
      <option value="hardware">Hardware (bare metal)</option>
      <option value="vm">VM</option>
    </select>
  </label>
</div>

{#if parentType === "hardware"}
  <label>
    Hardware
    <select bind:value={item.hardware_id}>
      <option value="">Select...</option>
      {#each hardwareOptions as hw}
        <option value={hw.id}>{hw.name}</option>
      {/each}
    </select>
  </label>
{:else if parentType === "vm"}
  <label>
    VM
    <select bind:value={item.vm_id}>
      <option value="">Select...</option>
      {#each vmOptions as vm}
        <option value={vm.id}>{vm.name}</option>
      {/each}
    </select>
  </label>
{/if}

<label>Description<input type="text" bind:value={item.description} /></label>
<div class="grid">
  <label>Hostname<input type="text" bind:value={item.hostname} placeholder="Defaults to parent hostname" /></label>
  <MultiInput
    label="IP Addresses"
    placeholder="Defaults to parent IP"
    values={ipAddresses}
    on:change={handleIpChange}
  />
</div>
<div class="grid">
  <label>External Hostname<input type="text" bind:value={item.external_hostname} /></label>
  <label>Port<input type="number" bind:value={item.port} /></label>
</div>
<label>
  <input type="checkbox" bind:checked={item.https} />
  Use HTTPS
</label>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
