<script>
  import Router from "svelte-spa-router";
  import { wrap } from "svelte-spa-router/wrap";
  import Layout from "./components/Layout.svelte";
  import InventoryPage from "./pages/InventoryPage.svelte";
  import Toast from "./components/Toast.svelte";

  const routes = {
    "/": InventoryPage,
    "/inventory": InventoryPage,
    "/inventory/:type": InventoryPage,
    "/inventory/:type/:id": InventoryPage,
    "/map": wrap({ asyncComponent: () => import("./pages/MapPage.svelte") }),
    "/scanner": wrap({ asyncComponent: () => import("./pages/ScannerPage.svelte") }),
    "/docs": wrap({ asyncComponent: () => import("./pages/DocsPage.svelte") }),
    "/docs/:id": wrap({ asyncComponent: () => import("./pages/DocsPage.svelte") }),
    "/settings": wrap({ asyncComponent: () => import("./pages/SettingsPage.svelte") }),
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
