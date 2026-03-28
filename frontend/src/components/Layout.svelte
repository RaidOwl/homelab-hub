<script>
  import Sidebar from "./Sidebar.svelte";
</script>

<div class="layout">
  <div class="content">
    <Sidebar />
    <main class="main">
      <slot />
    </main>
  </div>
</div>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .content {
    display: flex;
    flex: 1;
  }

  .main {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
  }
</style>
