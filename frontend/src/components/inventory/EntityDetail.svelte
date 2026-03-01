<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { get, post, put, del } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import HardwareForm from "./HardwareForm.svelte";
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
  let linkedDocs = [];

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
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
        
        // Load linked documents
        await loadLinkedDocs();
      } catch (e) {
        addToast(e.message, "error");
      }
      loading = false;
    }
  });

  async function loadLinkedDocs() {
    if (!id) return;
    try {
      // Map frontend route names to backend entity types
      const entityTypeMap = {
        'hardware': 'hardware',
        'vms': 'vm',
        'apps': 'app',
        'storage': 'storage',
        'networks': 'network',
        'misc': 'misc'
      };
      const entityType = entityTypeMap[type];
      const res = await get(`/docs?entity_type=${entityType}&entity_id=${id}`);
      linkedDocs = res.data;
    } catch (e) {
      console.error('Failed to load linked docs:', e);
    }
  }

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
  
  {#if id && linkedDocs.length > 0}
    <div class="linked-docs">
      <h4>📄 Related Documents</h4>
      <ul>
        {#each linkedDocs as doc}
          <li>
            <a href="#/docs/{doc.id}">{doc.title}</a>
          </li>
        {/each}
      </ul>
    </div>
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
  .linked-docs {
    margin-top: 2rem;
    max-width: 700px;
  }
  .linked-docs h4 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }
  .linked-docs ul {
    list-style: none;
    padding: 0;
  }
  .linked-docs li {
    padding: 0.4rem 0.5rem;
    border-radius: 4px;
  }
  .linked-docs li:hover {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.15));
  }
  .linked-docs a {
    text-decoration: none;
    color: var(--pico-primary, #6366f1);
  }
</style>
