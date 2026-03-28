<script>
  import { onDestroy } from "svelte";
  import { get, post } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";

  export let item = {};

  const IDENTIFY_TIMEOUT_MS = 60_000;
  const IDENTIFY_POLL_MS = 1500;

  let scanHostLoading = false;
  /** @type {ReturnType<typeof setTimeout> | null} */
  let identifyPollTimer = null;

  function clearIdentifyPoll() {
    if (identifyPollTimer) {
      clearTimeout(identifyPollTimer);
      identifyPollTimer = null;
    }
  }

  onDestroy(() => {
    clearIdentifyPoll();
  });

  /**
   * @param {Record<string, unknown>} row
   */
  function applyIdentifyResults(row) {
    const hn = row.hostname != null ? String(row.hostname).trim() : "";
    const mac = row.mac_address != null ? String(row.mac_address).trim() : "";
    const os = row.os != null ? String(row.os).trim() : "";

    if (hn) item.hostname = hn;
    if (mac) item.mac_address = mac;
    if (os) item.os = os;

    if (!hn) addToast("Could not detect hostname", "info");
    if (!mac) addToast("Could not detect MAC address", "info");
    if (!os) addToast("Could not detect OS", "info");

    if (hn && mac && os) {
      addToast("Host scan completed", "success");
    } else if (hn || mac || os) {
      addToast("Host scan completed (some fields could not be detected)", "success");
    }
  }

  /**
   * @param {string} scanId
   * @param {number} startedAt
   */
  async function pollIdentifyStatus(scanId, startedAt) {
    if (Date.now() - startedAt > IDENTIFY_TIMEOUT_MS) {
      clearIdentifyPoll();
      scanHostLoading = false;
      addToast("Scan timed out after 60 seconds", "error");
      return;
    }

    try {
      const res = await get(`/scanner/status/${scanId}`);
      const d = res.data;

      if (d.status === "failed") {
        clearIdentifyPoll();
        scanHostLoading = false;
        addToast(d.error || "Scan failed", "error");
        return;
      }

      if (d.status === "completed") {
        clearIdentifyPoll();
        scanHostLoading = false;
        const row = (d.results && d.results[0]) || {};
        applyIdentifyResults(row);
        return;
      }

      identifyPollTimer = setTimeout(
        () => void pollIdentifyStatus(scanId, startedAt),
        IDENTIFY_POLL_MS
      );
    } catch (e) {
      clearIdentifyPoll();
      scanHostLoading = false;
      const msg = e instanceof Error ? e.message : String(e);
      addToast(msg, "error");
    }
  }

  async function scanHost() {
    const ip = (item.ip_address || "").trim();
    if (!ip || scanHostLoading) return;

    clearIdentifyPoll();
    scanHostLoading = true;

    try {
      const start = await post("/scanner/identify", { target_ip: ip });
      const scanId = start.scan_id;
      const startedAt = Date.now();
      await pollIdentifyStatus(scanId, startedAt);
    } catch (e) {
      scanHostLoading = false;
      const msg = e instanceof Error ? e.message : String(e);
      addToast(msg, "error");
    }
  }

  $: ipPresent = !!(item.ip_address && String(item.ip_address).trim());
</script>

<span class="scan-host-controls">
  <button
    type="button"
    class="outline scan-host-btn"
    title="Detect hostname, MAC, and OS"
    aria-label="Scan host using IP address to detect hostname, MAC, and OS"
    aria-busy={scanHostLoading ? "true" : undefined}
    disabled={!ipPresent || scanHostLoading}
    on:click={scanHost}
  >
    {scanHostLoading ? "Scanning…" : "Scan Host"}
  </button>
</span>

<style>
  .scan-host-controls {
    display: inline-flex;
    align-items: baseline;
  }
  :global(.scan-host-btn) {
    font-size: 0.8rem;
    padding: 0.3rem 0.65rem;
    min-height: 0;
    line-height: 1.25;
    flex-shrink: 0;
  }
</style>
