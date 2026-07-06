<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};

  let hardwareOptions = [];
  let vmOptions = [];
  let lxcOptions = [];
  let parentType = item.vm_id ? "vm" : item.lxc_id ? "lxc" : item.hardware_id ? "hardware" : "none";

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
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>
    Runs on
    <select bind:value={parentType}>
      <option value="none">Standalone</option>
      <option value="hardware">Hardware</option>
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

<div class="grid">
  <label>Storage Type<input type="text" bind:value={item.storage_type} placeholder="HDD, SSD, NVMe..." /></label>
  <label>RAID Type<input type="text" bind:value={item.raid_type} placeholder="RAID-Z2, RAID 10..." /></label>
</div>
<div class="grid">
  <label>Drive Count<input type="number" bind:value={item.drive_count} /></label>
  <label>Raw Space (TB)<input type="number" step="0.01" bind:value={item.raw_space_tb} /></label>
  <label>Usable Space (TB)<input type="number" step="0.01" bind:value={item.usable_space_tb} /></label>
</div>
<label>Filesystem<input type="text" bind:value={item.filesystem} placeholder="ZFS, EXT4, BTRFS..." /></label>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
