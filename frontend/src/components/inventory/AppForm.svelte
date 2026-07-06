<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};

  let hardwareOptions = [];
  let vmOptions = [];
  let lxcOptions = [];
  let parentType = item.vm_id ? "vm" : item.lxc_id ? "lxc" : item.hardware_id ? "hardware" : "none";
  let previousHardwareId = item.hardware_id;
  let previousVmId = item.vm_id;
  let previousLxcId = item.lxc_id;

  onMount(async () => {
    try {
      const [hwRes, vmRes, lxcRes] = await Promise.all([get("/hardware"), get("/vms"), get("/lxcs")]);
      hardwareOptions = hwRes.data;
      vmOptions = vmRes.data;
      lxcOptions = lxcRes.data;
    } catch (e) {
      // ignore
    }
    if (item.vm_id) parentType = "vm";
    else if (item.lxc_id) parentType = "lxc";
    else if (item.hardware_id) parentType = "hardware";
  });

  $: {
    if (parentType === "none") {
      item.hardware_id = null;
      item.vm_id = null;
      item.lxc_id = null;
    } else if (parentType === "hardware") {
      item.vm_id = null;
      item.lxc_id = null;
    } else if (parentType === "vm") {
      item.hardware_id = null;
      item.lxc_id = null;
    } else if (parentType === "lxc") {
      item.hardware_id = null;
      item.vm_id = null;
    }
  }

  // Auto-populate hostname and IP from parent only when creating a new app
  $: if (!item.id && item.hardware_id && hardwareOptions.length > 0 && item.hardware_id !== previousHardwareId) {
    const hardware = hardwareOptions.find(h => h.id === item.hardware_id);
    if (hardware) {
      if (hardware.hostname && !item.hostname) {
        item.hostname = hardware.hostname;
      }
      if (hardware.ip_address && !item.ip_address) {
        item.ip_address = hardware.ip_address;
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
      if (vm.ip_address && !item.ip_address) {
        item.ip_address = vm.ip_address;
      }
    }
    previousVmId = item.vm_id;
  }
  $: if (!item.id && item.lxc_id && lxcOptions.length > 0 && item.lxc_id !== previousLxcId) {
    const lxc = lxcOptions.find(l => l.id === item.lxc_id);
    if (lxc) {
      if (lxc.hostname && !item.hostname) {
        item.hostname = lxc.hostname;
      }
      if (lxc.ip_address && !item.ip_address) {
        item.ip_address = lxc.ip_address;
      }
    }
    previousLxcId = item.lxc_id;
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
      <option value="lxc">LXC</option>
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
{:else if parentType === "lxc"}
  <label>
    LXC
    <select bind:value={item.lxc_id}>
      <option value="">Select...</option>
      {#each lxcOptions as lxc}
        <option value={lxc.id}>{lxc.name}</option>
      {/each}
    </select>
  </label>
{/if}

<label>Description<input type="text" bind:value={item.description} /></label>
<div class="grid">
  <label>Hostname<input type="text" bind:value={item.hostname} placeholder="Defaults to parent hostname" /></label>
  <label>IP Address<input type="text" bind:value={item.ip_address} placeholder="Defaults to parent IP" /></label>
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
