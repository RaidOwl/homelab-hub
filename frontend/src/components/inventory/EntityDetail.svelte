<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { get, post, put, del } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import HardwareForm from "./HardwareForm.svelte";
  import ScanHostControls from "./ScanHostControls.svelte";
  import ScanAppControls from "./ScanAppControls.svelte";
  import VmForm from "./VmForm.svelte";
  import AppForm from "./AppForm.svelte";
  import StorageForm from "./StorageForm.svelte";
  import NetworkForm from "./NetworkForm.svelte";
  import MiscForm from "./MiscForm.svelte";
  import ShareList from "./ShareList.svelte";

  export let type;
  export let id = null;

  const dispatch = createEventDispatcher();

  let item = {};
  let loading = !!id;
  let shares = [];
  let parentIp = '';
  let parentHostname = '';
  /** Resolved host IP for Scan App when app row has no ip_address */
  let appParentIp = '';
  let appParentIpCacheKey = '';
  let appParentIpFetchSerial = 0;

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
    apps: AppForm,
    storage: StorageForm,
    networks: NetworkForm,
    misc: MiscForm,
  };

  $: FormComponent = FORMS[type];

  async function loadAppParentIpForScan(hwId, vmId) {
    const key = `${hwId ?? ""}|${vmId ?? ""}`;
    if (key === appParentIpCacheKey) return;
    appParentIpCacheKey = key;
    appParentIp = "";
    if (!hwId && !vmId) return;
    const serial = ++appParentIpFetchSerial;
    try {
      let ip = "";
      if (hwId) {
        const hwRes = await get(`/hardware/${hwId}`);
        ip = hwRes.data.ip_address || "";
      } else if (vmId) {
        const vmRes = await get(`/vms/${vmId}`);
        ip = vmRes.data.ip_address || "";
      }
      if (serial === appParentIpFetchSerial) appParentIp = ip;
    } catch {
      if (serial === appParentIpFetchSerial) appParentIp = "";
    }
  }

  $: if (type === "apps") {
    void loadAppParentIpForScan(item.hardware_id, item.vm_id);
  } else {
    appParentIp = "";
    appParentIpCacheKey = "";
  }

  onMount(async () => {
    if (id) {
      try {
        const res = await get(`/${type}/${id}`);
        item = res.data;
        if (type === 'storage' && item.shares) {
          shares = item.shares;
          
          // Fetch grandparent (hardware or vm) details for default IP/hostname
          if (item.hardware_id) {
            const hwRes = await get(`/hardware/${item.hardware_id}`);
            parentIp = hwRes.data.ip_address || '';
            parentHostname = hwRes.data.hostname || '';
          } else if (item.vm_id) {
            const vmRes = await get(`/vms/${item.vm_id}`);
            parentIp = vmRes.data.ip_address || '';
            parentHostname = vmRes.data.hostname || '';
          }
        }
      } catch (e) {
        addToast(e.message, "error");
      }
      loading = false;
    }
  });

  async function handleSubmit() {
    try {
      if (id) {
        await put(`/${type}/${id}`, item);
        addToast("Updated", "success");
      } else {
        await post(`/${type}`, item);
        addToast("Created", "success");
      }
      dispatch("saved");
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function handleShareSave(event) {
    try {
      const shareData = event.detail;
      
      if (shareData.id) {
        // Update existing share
        await put(`/shares/${shareData.id}`, shareData);
        addToast("Share updated", "success");
      } else {
        // Create new share
        const result = await post('/shares', shareData);
        addToast("Share created", "success");
      }
      
      // Reload the storage item to get updated shares
      const res = await get(`/${type}/${id}`);
      item = res.data;
      shares = item.shares || [];
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function handleShareDelete(event) {
    try {
      const share = event.detail;
      await del(`/shares/${share.id}`);
      addToast("Share deleted", "success");
      
      // Reload the storage item to get updated shares
      const res = await get(`/${type}/${id}`);
      item = res.data;
      shares = item.shares || [];
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

{#if loading}
  <p aria-busy="true">Loading...</p>
{:else}
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-title-row">
      <div class="form-title-cluster">
        <h3>{id ? "Edit" : "New"} {type.charAt(0).toUpperCase() + type.slice(1).replace(/s$/, "")}</h3>
        {#if type === "hardware"}
          <ScanHostControls bind:item />
        {:else if type === "apps"}
          <ScanAppControls bind:item parentIp={appParentIp} />
        {/if}
      </div>
      <button type="submit" class="header-submit">{id ? "Save" : "Create"}</button>
    </div>

    <svelte:component this={FormComponent} bind:item />
  </form>
  
  {#if type === 'storage' && id}
    <ShareList 
      {shares}
      storageId={id}
      {parentIp}
      {parentHostname}
      on:save={handleShareSave}
      on:delete={handleShareDelete}
    />
  {/if}
{/if}

<style>
  .form-title-row {
    display: flex;
    flex-wrap: nowrap;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .form-title-cluster {
    display: flex;
    flex-wrap: nowrap;
    align-items: baseline;
    gap: 0.75rem 1.25rem;
    min-width: 0;
    flex: 1 1 auto;
  }
  .form-title-cluster h3 {
    margin: 0;
    flex-shrink: 0;
  }
  .header-submit {
    width: 128px;
    flex-shrink: 0;
    margin-left: auto;
    font-size: 0.8rem;
    padding: 0.3rem 0.65rem;
    min-height: 0;
    line-height: 1.25;
  }
  form {
    max-width: 700px;
  }

  @media (max-width: 767px) {
    .form-title-row {
      flex-wrap: wrap;
    }
    .form-title-row .form-title-cluster {
      width: 100%;
    }
  }
</style>
