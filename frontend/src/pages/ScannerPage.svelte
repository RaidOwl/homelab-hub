<script>
  import { onMount, onDestroy } from "svelte";
  import { get, post } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";
  import ScanProgress from "../components/scanner/ScanProgress.svelte";
  import ScanResultsTable from "../components/scanner/ScanResultsTable.svelte";

  const DISCOVER_KEY = "scanner:discover";
  const PORTSCAN_KEY = "scanner:portscan";

  let subnetHints = [];
  let subnet = "";
  let discoverScanId = null;
  let discoverStatus = "idle";
  let discoverProgress = 0;
  let discoverError = null;
  let discoverRows = [];
  let selectedHostIds = [];

  let hardwareList = [];
  let vmList = [];
  let parentType = "hardware";
  let parentId = "";
  let portRange = "1-1024";
  let portScanId = null;
  let portStatus = "idle";
  let portProgress = 0;
  let portError = null;
  let portRows = [];
  let selectedPortIds = [];

  /** @type {ReturnType<typeof setInterval> | null} */
  let discoverPollInterval = null;
  /** @type {ReturnType<typeof setInterval> | null} */
  let portPollInterval = null;

  function persistDiscover() {
    try {
      localStorage.setItem(
        DISCOVER_KEY,
        JSON.stringify({
          scanId: discoverScanId,
          status: discoverStatus,
          progress: discoverProgress,
          rows: discoverRows,
          subnet,
          error: discoverError,
        })
      );
    } catch {
      /* quota or private mode */
    }
  }

  function persistPortScan() {
    try {
      localStorage.setItem(
        PORTSCAN_KEY,
        JSON.stringify({
          scanId: portScanId,
          status: portStatus,
          progress: portProgress,
          rows: portRows,
          targetIp,
          parentType,
          parentId: parentId === "" || parentId == null ? "" : String(parentId),
          portRange,
          error: portError,
        })
      );
    } catch {
      /* quota or private mode */
    }
  }

  function clearDiscoverResults() {
    if (discoverPollInterval) {
      clearInterval(discoverPollInterval);
      discoverPollInterval = null;
    }
    discoverScanId = null;
    discoverRows = [];
    discoverStatus = "idle";
    discoverProgress = 0;
    discoverError = null;
    selectedHostIds = [];
    try {
      localStorage.removeItem(DISCOVER_KEY);
    } catch {
      /* ignore */
    }
  }

  function clearPortResults() {
    if (portPollInterval) {
      clearInterval(portPollInterval);
      portPollInterval = null;
    }
    portScanId = null;
    portRows = [];
    portStatus = "idle";
    portProgress = 0;
    portError = null;
    selectedPortIds = [];
    try {
      localStorage.removeItem(PORTSCAN_KEY);
    } catch {
      /* ignore */
    }
  }

  function stopDiscoverPoll() {
    if (discoverPollInterval) {
      clearInterval(discoverPollInterval);
      discoverPollInterval = null;
    }
  }

  function stopPortPoll() {
    if (portPollInterval) {
      clearInterval(portPollInterval);
      portPollInterval = null;
    }
  }

  /**
   * @param {string} scanId
   * @param {{ resume?: boolean }} [opts]
   */
  function startDiscoverPolling(scanId, opts = {}) {
    stopDiscoverPoll();
    discoverPollInterval = setInterval(async () => {
      try {
        const res = await get(`/scanner/status/${scanId}`);
        const d = res.data;
        if (d.status === "expired") {
          stopDiscoverPoll();
          clearDiscoverResults();
          addToast("Previous discovery expired. Start a new scan.", "info");
          return;
        }
        discoverProgress = d.progress ?? 0;
        discoverStatus = d.status;
        if (d.status === "failed") {
          stopDiscoverPoll();
          discoverError = d.error || "Failed";
          persistDiscover();
          if (!opts.resume) addToast(discoverError, "error");
        } else if (d.status === "completed") {
          stopDiscoverPoll();
          discoverRows = d.results || [];
          discoverProgress = 100;
          persistDiscover();
          if (!opts.resume) {
            addToast(`Found ${discoverRows.length} host(s)`, "success");
          }
        } else {
          persistDiscover();
        }
      } catch (e) {
        stopDiscoverPoll();
        const msg = e instanceof Error ? e.message : String(e);
        discoverError = msg;
        discoverStatus = "failed";
        persistDiscover();
        if (!opts.resume) addToast(msg, "error");
      }
    }, 400);
  }

  /**
   * @param {string} scanId
   * @param {{ resume?: boolean }} [opts]
   */
  function startPortPolling(scanId, opts = {}) {
    stopPortPoll();
    portPollInterval = setInterval(async () => {
      try {
        const res = await get(`/scanner/status/${scanId}`);
        const d = res.data;
        if (d.status === "expired") {
          stopPortPoll();
          clearPortResults();
          addToast("Previous port scan expired. Start a new scan.", "info");
          return;
        }
        portProgress = d.progress ?? 0;
        portStatus = d.status;
        if (d.status === "failed") {
          stopPortPoll();
          portError = d.error || "Failed";
          persistPortScan();
          if (!opts.resume) addToast(portError, "error");
        } else if (d.status === "completed") {
          stopPortPoll();
          portRows = d.results || [];
          portProgress = 100;
          persistPortScan();
          if (!opts.resume) {
            addToast(`Found ${portRows.length} open port(s)`, "success");
          }
        } else {
          persistPortScan();
        }
      } catch (e) {
        stopPortPoll();
        const msg = e instanceof Error ? e.message : String(e);
        portError = msg;
        portStatus = "failed";
        persistPortScan();
        if (!opts.resume) addToast(msg, "error");
      }
    }, 400);
  }

  function loadPersistedScannerState() {
    try {
      const raw = localStorage.getItem(DISCOVER_KEY);
      if (!raw) {
        /* no-op */
      } else {
        const d = JSON.parse(raw);
        if (d && typeof d === "object") {
          if (d.subnet) subnet = d.subnet;
          discoverScanId = d.scanId ?? null;
          discoverStatus = d.status || "idle";
          discoverProgress = d.progress ?? 0;
          discoverRows = Array.isArray(d.rows) ? d.rows : [];
          discoverError = d.error ?? null;
          if (discoverStatus === "running" && discoverScanId) {
            startDiscoverPolling(discoverScanId, { resume: true });
          }
        }
      }
    } catch {
      try {
        localStorage.removeItem(DISCOVER_KEY);
      } catch {
        /* ignore */
      }
    }
    try {
      const raw = localStorage.getItem(PORTSCAN_KEY);
      if (!raw) {
        /* no-op */
      } else {
        const p = JSON.parse(raw);
        if (p && typeof p === "object") {
          parentType = p.parentType === "vm" ? "vm" : "hardware";
          if (p.parentId !== undefined && p.parentId !== null && p.parentId !== "") {
            parentId = String(p.parentId);
          }
          if (p.portRange) portRange = p.portRange;
          portScanId = p.scanId ?? null;
          portStatus = p.status || "idle";
          portProgress = p.progress ?? 0;
          portRows = Array.isArray(p.rows) ? p.rows : [];
          portError = p.error ?? null;
          if (portStatus === "running" && portScanId) {
            startPortPolling(portScanId, { resume: true });
          }
        }
      }
    } catch {
      try {
        localStorage.removeItem(PORTSCAN_KEY);
      } catch {
        /* ignore */
      }
    }
  }

  onDestroy(() => {
    stopDiscoverPoll();
    stopPortPoll();
  });

  const portPresets = [
    { label: "1–1024 (common)", value: "1-1024" },
    { label: "Top 100 ports", value: "1-100" },
    { label: "1–65535 (slow)", value: "1-65535" },
  ];

  const hostColumns = [
    { key: "ip", label: "IP" },
    { key: "hostname", label: "Hostname" },
    { key: "mac", label: "MAC" },
    { key: "vendor", label: "Vendor" },
  ];

  const portColumns = [
    { key: "port", label: "Port" },
    { key: "protocol", label: "Proto" },
    { key: "service_name", label: "Service" },
    { key: "service_version", label: "Version" },
    {
      key: "http_title",
      label: "HTTP title",
    },
  ];

  function normalizeMac(m) {
    if (!m) return null;
    return String(m).replace(/-/g, ":").trim().toUpperCase();
  }

  function hardwareHasHost(row) {
    const mac = normalizeMac(row.mac);
    return hardwareList.some(
      (h) =>
        h.ip_address === row.ip ||
        (mac && h.mac_address && normalizeMac(h.mac_address) === mac)
    );
  }

  $: portRowsDisplay = portRows.map((r) => ({
    ...r,
    http_title: r.http_probe?.title ?? "",
  }));

  $: targetIp =
    parentType === "hardware"
      ? hardwareList.find((h) => h.id === Number(parentId))?.ip_address || ""
      : vmList.find((v) => v.id === Number(parentId))?.ip_address || "";

  onMount(async () => {
    try {
      const ifRes = await get("/scanner/interfaces");
      subnetHints = ifRes.data || [];
      if (subnetHints.length && !subnet) {
        subnet = subnetHints[0].subnet;
      }
    } catch (e) {
      addToast(e.message, "error");
    }
    await loadInventoryParents();
    loadPersistedScannerState();
  });

  async function loadInventoryParents() {
    try {
      const [hwRes, vmRes] = await Promise.all([get("/hardware"), get("/vms")]);
      hardwareList = hwRes.data || [];
      vmList = vmRes.data || [];
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function runDiscover() {
    if (!subnet.trim()) {
      addToast("Enter a subnet (CIDR)", "error");
      return;
    }
    stopDiscoverPoll();
    try {
      localStorage.removeItem(DISCOVER_KEY);
    } catch {
      /* ignore */
    }
    discoverError = null;
    discoverStatus = "running";
    discoverProgress = 0;
    discoverRows = [];
    selectedHostIds = [];
    discoverScanId = null;
    try {
      const start = await post("/scanner/discover", { subnet: subnet.trim() });
      discoverScanId = start.scan_id;
      persistDiscover();
      startDiscoverPolling(discoverScanId);
    } catch (e) {
      discoverStatus = "failed";
      discoverError = e.message;
      persistDiscover();
      addToast(e.message, "error");
    }
  }

  async function importHosts() {
    const selected = discoverRows.filter((r) => selectedHostIds.includes(r.ip));
    if (!selected.length) {
      addToast("Select at least one host", "error");
      return;
    }
    const hosts = selected.map((r) => ({
      ip: r.ip,
      name: r.hostname || r.ip,
      hostname: r.hostname || null,
      mac: r.mac || null,
    }));
    try {
      const res = await post("/scanner/import/hardware", { hosts });
      addToast(
        `Imported ${res.created?.length || 0}, skipped ${res.skipped?.length || 0}`,
        "success"
      );
      selectedHostIds = [];
      await loadInventoryParents();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function runPortScan() {
    if (!targetIp) {
      addToast("Select a hardware or VM with an IP address", "error");
      return;
    }
    stopPortPoll();
    try {
      localStorage.removeItem(PORTSCAN_KEY);
    } catch {
      /* ignore */
    }
    portError = null;
    portStatus = "running";
    portProgress = 0;
    portRows = [];
    selectedPortIds = [];
    portScanId = null;
    try {
      const start = await post("/scanner/portscan", {
        target_ip: targetIp,
        port_range: portRange,
      });
      portScanId = start.scan_id;
      persistPortScan();
      startPortPolling(portScanId);
    } catch (e) {
      portStatus = "failed";
      portError = e.message;
      persistPortScan();
      addToast(e.message, "error");
    }
  }

  async function importApps() {
    const pid = parentId === "" || parentId == null ? NaN : Number(parentId);
    if (Number.isNaN(pid)) {
      addToast("Select parent hardware or VM", "error");
      return;
    }
    const hid = parentType === "hardware" ? pid : null;
    const vid = parentType === "vm" ? pid : null;
    const selected = portRows.filter((r) =>
      selectedPortIds.includes(String(r.port))
    );
    if (!selected.length) {
      addToast("Select at least one port", "error");
      return;
    }
    const services = selected.map((r) => ({
      name:
        r.http_probe?.suggested_name ||
        r.service_name ||
        `Port ${r.port}`,
      port: r.port,
      https: Boolean(r.https),
      description: [r.service_version, r.banner].filter(Boolean).join(" ").trim() || null,
      http_probe: r.http_probe || null,
    }));
    try {
      const body =
        hid != null
          ? { hardware_id: hid, services }
          : { vm_id: vid, services };
      const res = await post("/scanner/import/apps", body);
      addToast(
        `Created ${res.created?.length || 0} app(s), skipped ${res.skipped?.length || 0}`,
        "success"
      );
      selectedPortIds = [];
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

<div class="scanner-page">
  <header class="page-head">
    <h1>Network scanner</h1>
    <p class="lead">
      Discover hosts on your LAN, import them as hardware, then scan open ports and add services as apps.
    </p>
  </header>

  <section class="card" aria-labelledby="lan-heading">
    <h2 id="lan-heading">1. LAN discovery</h2>
    <div class="row">
      <label>
        Subnet (CIDR)
        <input type="text" bind:value={subnet} placeholder="192.168.1.0/24" />
      </label>
      {#if subnetHints.length}
        <label>
          Quick pick
          <select bind:value={subnet}>
            {#each subnetHints as h}
              <option value={h.subnet}>{h.label}</option>
            {/each}
          </select>
        </label>
      {/if}
      <button
        type="button"
        on:click={runDiscover}
        disabled={discoverStatus === "running"}
      >
        Scan network
      </button>
    </div>
    <ScanProgress
      status={discoverStatus}
      progress={discoverProgress}
      error={discoverError}
      label="Discovering hosts on the LAN…"
    />
    {#if discoverRows.length}
      <ScanResultsTable
        columns={hostColumns}
        rows={discoverRows}
        rowId={(row) => row.ip}
        bind:selectedIds={selectedHostIds}
        rowBadge={(row) => (hardwareHasHost(row) ? "In inventory" : null)}
      />
    {/if}
    {#if discoverRows.length || discoverStatus === "completed" || discoverStatus === "failed"}
      <div class="actions">
        {#if discoverRows.length}
          <button type="button" on:click={importHosts} disabled={!selectedHostIds.length}>
            Import selected as hardware
          </button>
          <a href="#/inventory/hardware" class="secondary">View hardware</a>
        {/if}
        <button
          type="button"
          class="outline secondary"
          on:click={clearDiscoverResults}
        >
          Clear results
        </button>
      </div>
    {/if}
  </section>

  <section class="card" aria-labelledby="port-heading">
    <h2 id="port-heading">2. Port scan → apps</h2>
    <div class="row grid-parent">
      <label>
        Parent
        <select bind:value={parentType}>
          <option value="hardware">Hardware</option>
          <option value="vm">VM</option>
        </select>
      </label>
      <label>
        Machine
        <select bind:value={parentId}>
          <option value="">Select…</option>
          {#if parentType === "hardware"}
            {#each hardwareList as h}
              <option value={h.id}>{h.name} — {h.ip_address || "no IP"}</option>
            {/each}
          {:else}
            {#each vmList as v}
              <option value={v.id}>{v.name} — {v.ip_address || "no IP"}</option>
            {/each}
          {/if}
        </select>
      </label>
      <label>
        Port range
        <select bind:value={portRange}>
          {#each portPresets as p}
            <option value={p.value}>{p.label}</option>
          {/each}
        </select>
      </label>
      <label class="wide">
        Custom range
        <input
          type="text"
          bind:value={portRange}
          placeholder="e.g. 22,80,443 or 1-1024"
        />
      </label>
    </div>
    <p class="target">
      Target IP: <strong>{targetIp || "—"}</strong>
    </p>
    <button
      type="button"
      on:click={runPortScan}
      disabled={portStatus === "running" || !targetIp}
    >
      Scan ports
    </button>
    <ScanProgress
      status={portStatus}
      progress={portProgress}
      error={portError}
      label="Scanning TCP ports…"
    />
    {#if portRows.length}
      <ScanResultsTable
        columns={portColumns}
        rows={portRowsDisplay}
        rowId={(row) => String(row.port)}
        bind:selectedIds={selectedPortIds}
      />
    {/if}
    {#if portRows.length || portStatus === "completed" || portStatus === "failed"}
      <div class="actions">
        {#if portRows.length}
          <button type="button" on:click={importApps} disabled={!selectedPortIds.length}>
            Import selected as apps
          </button>
          <a href="#/inventory/apps" class="secondary">View apps</a>
        {/if}
        <button
          type="button"
          class="outline secondary"
          on:click={clearPortResults}
        >
          Clear results
        </button>
      </div>
    {/if}
  </section>
</div>

<style>
  .scanner-page {
    padding: 1rem 1.5rem 2rem;
    max-width: 1100px;
  }
  .page-head h1 {
    margin-bottom: 0.25rem;
  }
  .lead {
    color: var(--pico-muted-color, #aaa);
    margin-top: 0;
    max-width: 52rem;
  }
  .card {
    background: var(--pico-card-background-color, #16161f);
    border: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
  }
  .card h2 {
    margin-top: 0;
    font-size: 1.1rem;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-end;
  }
  .row label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 12rem;
  }
  .row .wide {
    flex: 1;
    min-width: 200px;
  }
  .target {
    font-size: 0.9rem;
    color: var(--pico-muted-color, #aaa);
  }
  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-top: 1rem;
    flex-wrap: wrap;
  }
  a.secondary {
    color: var(--pico-primary, #6366f1);
  }
</style>
