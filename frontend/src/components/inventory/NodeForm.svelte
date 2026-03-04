<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};

  let clusterOptions = [];

  onMount(async () => {
    try {
      const res = await get("/clusters");
      clusterOptions = res.data;
    } catch (e) {
      // ignore
    }
  });
</script>

<div class="grid">
  <label>Name *<input type="text" bind:value={item.name} required /></label>
  <label>
    Cluster
    <select bind:value={item.cluster_id}>
      <option value="">No cluster</option>
      {#each clusterOptions as cluster}
        <option value={cluster.id}>{cluster.name}</option>
      {/each}
    </select>
  </label>
</div>
<div class="grid">
  <label>Hostname<input type="text" bind:value={item.hostname} /></label>
  <label>IP Address<input type="text" bind:value={item.ip_address} /></label>
</div>
<div class="grid">
  <label>MAC Address<input type="text" bind:value={item.mac_address} placeholder="00:00:00:00:00:00" /></label>
  <label>OS<input type="text" bind:value={item.os} /></label>
</div>
<div class="grid">
  <label>CPU<input type="text" bind:value={item.cpu} /></label>
  <label>CPU Cores<input type="number" bind:value={item.cpu_cores} /></label>
  <label>RAM (GB)<input type="number" step="0.1" bind:value={item.ram_gb} /></label>
</div>
<IconPicker bind:value={item.icon} />
<label>Notes<textarea bind:value={item.notes} rows="3"></textarea></label>
