<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { get, post, put, del } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import HardwareForm from "./HardwareForm.svelte";
  import VmForm from "./VmForm.svelte";
  import LxcForm from "./LxcForm.svelte";
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

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
    lxcs: LxcForm,
    apps: AppForm,
    storage: StorageForm,
    networks: NetworkForm,
    misc: MiscForm,
  };

  $: FormComponent = FORMS[type];

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
    <h3>{id ? "Edit" : "New"} {type.charAt(0).toUpperCase() + type.slice(1).replace(/s$/, "")}</h3>

    <svelte:component this={FormComponent} bind:item />

    <div class="form-actions">
      <button type="submit">{id ? "Save" : "Create"}</button>
      <button type="button" class="outline secondary" on:click={() => {
        dispatch("cancel");
        if (id) history.back();
      }}>
        Cancel
      </button>
    </div>
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
  .form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  form {
    max-width: 700px;
  }
</style>
