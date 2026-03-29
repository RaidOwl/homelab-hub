<script>
  import { params } from "svelte-spa-router";
  import { onMount } from "svelte";
  import { get, post, put, del } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";
  import DocEditor from "../components/docs/DocEditor.svelte";

  let docs = [];
  let activeDoc = null;
  let loading = true;
  let saveTimeout;

  $: docId = $params?.id ? parseInt($params.id) : null;

  async function loadDocs() {
    try {
      const res = await get("/docs");
      docs = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
    loading = false;
  }

  async function loadDoc(id) {
    if (!id) {
      activeDoc = null;
      return;
    }
    try {
      const res = await get(`/docs/${id}`);
      activeDoc = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  $: loadDoc(docId);
  onMount(loadDocs);

  async function createDoc() {
    try {
      const res = await post("/docs", { title: "Untitled" });
      docs = [...docs, res.data];
      window.location.hash = `/docs/${res.data.id}`;
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function deleteDoc(id) {
    if (!confirm("Delete this document?")) return;
    try {
      await del(`/docs/${id}`);
      addToast("Deleted", "success");
      if (activeDoc?.id === id) {
        activeDoc = null;
        window.location.hash = "/docs";
      }
      loadDocs();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  function handleContentChange(content) {
    if (!activeDoc) return;
    activeDoc.content = content;
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      try {
        await put(`/docs/${activeDoc.id}`, {
          title: activeDoc.title,
          content: activeDoc.content,
        });
      } catch (e) {
        addToast("Auto-save failed: " + e.message, "error");
      }
    }, 1000);
  }

  async function handleTitleChange() {
    if (!activeDoc) return;
    try {
      await put(`/docs/${activeDoc.id}`, { title: activeDoc.title });
      const idx = docs.findIndex((d) => d.id === activeDoc.id);
      if (idx !== -1) docs[idx].title = activeDoc.title;
      docs = docs;
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

<div class="docs-page">
  <aside class="doc-list">
    <div class="doc-list-header">
      <h3>Documents</h3>
      <button class="outline small" on:click={createDoc}>+ New</button>
    </div>
    {#if loading}
      <p aria-busy="true">Loading...</p>
    {:else}
      <ul>
        {#each docs as doc (doc.id)}
          <li class:active={activeDoc?.id === doc.id}>
            <a href={"#/docs/" + doc.id}>{doc.title}</a>
            <button class="delete-btn" on:click|stopPropagation={() => deleteDoc(doc.id)}>x</button>
          </li>
        {/each}
      </ul>
    {/if}
  </aside>

  <div class="doc-content">
    {#if activeDoc}
      <input
        class="doc-title"
        type="text"
        bind:value={activeDoc.title}
        on:blur={handleTitleChange}
      />
      <DocEditor content={activeDoc.content} onChange={handleContentChange} />
    {:else}
      <p class="placeholder">Select a document or create a new one.</p>
    {/if}
  </div>
</div>

<style>
  .docs-page {
    display: flex;
    gap: 0;
    height: calc(100vh - 3rem);
  }
  .doc-list {
    width: 240px;
    border-right: 1px solid var(--pico-muted-border-color, #333);
    padding: 1rem;
    overflow-y: auto;
    flex-shrink: 0;
  }
  .doc-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  .doc-list-header h3 {
    margin: 0;
    font-size: 1rem;
  }
  .doc-list-header button {
    padding: 0.2rem 0.5rem;
    font-size: 0.8rem;
    margin: 0;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0.5rem;
    border-radius: 4px;
  }
  li.active {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.15));
  }
  li.active a {
    color: rgba(255, 255, 255, 1);
  }
  li a {
    text-decoration: none;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .delete-btn {
    background: none;
    border: none;
    color: var(--pico-muted-color, #666);
    cursor: pointer;
    padding: 0 0.3rem;
    font-size: 0.8rem;
    margin: 0;
  }
  .doc-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .doc-title {
    font-size: 1.4rem;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 0;
    margin-bottom: 0;
    padding: 0.5rem;
  }
  .placeholder {
    padding: 2rem;
    color: var(--pico-muted-color, #666);
  }
</style>
