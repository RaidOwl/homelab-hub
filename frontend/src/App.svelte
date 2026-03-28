<script>
  import Router from "svelte-spa-router";
  import Layout from "./components/Layout.svelte";
  import DocsPage from "./pages/DocsPage.svelte";
  import InventoryPage from "./pages/InventoryPage.svelte";
  import MapPage from "./pages/MapPage.svelte";
  import ScannerPage from "./pages/ScannerPage.svelte";
  import SettingsPage from "./pages/SettingsPage.svelte";
  import Toast from "./components/Toast.svelte";

  const routes = {
    "/": InventoryPage,
    "/inventory": InventoryPage,
    "/inventory/:type": InventoryPage,
    "/inventory/:type/:id": InventoryPage,
    "/map": MapPage,
    "/scanner": ScannerPage,
    "/docs": DocsPage,
    "/docs/:id": DocsPage,
    "/settings": SettingsPage,
  };
</script>

<Layout>
  <Router {routes} />
</Layout>
<Toast />

<style>
  :global(body) {
    margin: 0;
    min-height: 100vh;
  }
  :global(#app) {
    min-height: 100vh;
  }
</style>
