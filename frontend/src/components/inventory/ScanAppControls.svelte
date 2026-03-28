<script>
  import { onDestroy } from "svelte";
  import { get, post } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";

  export let item = {};
  /** Host IP from parent hardware/VM when app.ip_address is blank */
  export let parentIp = "";

  const PROBE_TIMEOUT_MS = 60_000;
  const PROBE_POLL_MS = 1500;

  /** Default-style names from scanner import (e.g. "Port 443") */
  const PORT_DEFAULT_NAME = /^Port\s+\d+$/i;

  let scanAppLoading = false;
  /** @type {ReturnType<typeof setTimeout> | null} */
  let probePollTimer = null;

  function clearProbePoll() {
    if (probePollTimer) {
      clearTimeout(probePollTimer);
      probePollTimer = null;
    }
  }

  onDestroy(() => {
    clearProbePoll();
  });

  /**
   * @param {string | undefined | null} name
   */
  function shouldApplyDetectedName(name) {
    const n = name != null ? String(name).trim() : "";
    return !n || PORT_DEFAULT_NAME.test(n);
  }

  /**
   * Port for HTTP probe: explicit app port, or 443/80 from HTTPS checkbox when unset.
   * @param {unknown} rawPort
   * @param {boolean} https
   */
  function resolveProbePort(rawPort, https) {
    const p =
      rawPort === null || rawPort === undefined || rawPort === ""
        ? NaN
        : Number(rawPort);
    if (!Number.isNaN(p) && p >= 1 && p <= 65535) return p;
    return https ? 443 : 80;
  }

  /**
   * @param {Record<string, unknown>} row
   */
  function applyProbeResults(row) {
    const err = row.error != null ? String(row.error).trim() : "";
    if (err) {
      addToast(err, "error");
      return;
    }

    const suggested =
      row.suggested_name != null ? String(row.suggested_name).trim() : "";
    if (!suggested) {
      addToast("Could not detect a name from the web UI", "info");
      return;
    }

    if (shouldApplyDetectedName(item.name)) {
      item.name = suggested;
      addToast(`Name set to "${suggested}"`, "success");
    } else {
      addToast(
        `Detected "${suggested}" — not overwriting the current name`,
        "info"
      );
    }
  }

  /**
   * @param {string} scanId
   * @param {number} startedAt
   */
  async function pollProbeStatus(scanId, startedAt) {
    if (Date.now() - startedAt > PROBE_TIMEOUT_MS) {
      clearProbePoll();
      scanAppLoading = false;
      addToast("Scan timed out after 60 seconds", "error");
      return;
    }

    try {
      const res = await get(`/scanner/status/${scanId}`);
      const d = res.data;

      if (d.status === "failed") {
        clearProbePoll();
        scanAppLoading = false;
        addToast(d.error || "Scan failed", "error");
        return;
      }

      if (d.status === "completed") {
        clearProbePoll();
        scanAppLoading = false;
        const row = (d.results && d.results[0]) || {};
        applyProbeResults(row);
        return;
      }

      probePollTimer = setTimeout(
        () => void pollProbeStatus(scanId, startedAt),
        PROBE_POLL_MS
      );
    } catch (e) {
      clearProbePoll();
      scanAppLoading = false;
      const msg = e instanceof Error ? e.message : String(e);
      addToast(msg, "error");
    }
  }

  async function scanApp() {
    const ip = (
      (item.ip_address != null ? String(item.ip_address) : "").trim() ||
      (parentIp != null ? String(parentIp) : "").trim()
    );
    const portNum = resolveProbePort(item.port, !!item.https);
    if (!ip || scanAppLoading) return;

    clearProbePoll();
    scanAppLoading = true;

    try {
      const start = await post("/scanner/probe-http", {
        target_ip: ip,
        port: portNum,
        https: !!item.https,
      });
      const scanId = start.scan_id;
      const startedAt = Date.now();
      await pollProbeStatus(scanId, startedAt);
    } catch (e) {
      scanAppLoading = false;
      const msg = e instanceof Error ? e.message : String(e);
      addToast(msg, "error");
    }
  }

  $: effectiveIp =
    (item.ip_address != null ? String(item.ip_address) : "").trim() ||
    (parentIp != null ? String(parentIp) : "").trim();
  $: probePort = resolveProbePort(item.port, !!item.https);
  $: canScan = !!effectiveIp && probePort >= 1 && probePort <= 65535;
</script>

<span class="scan-app-controls">
  <button
    type="button"
    class="outline scan-app-btn"
    title="Uses IP (and port if set; otherwise 80 or 443 from HTTPS). Fetches page title or meta tags."
    aria-label="Scan web UI to detect app name from title or meta tags"
    aria-busy={scanAppLoading ? "true" : undefined}
    disabled={!canScan || scanAppLoading}
    on:click={scanApp}
  >
    {scanAppLoading ? "Scanning…" : "Scan App"}
  </button>
</span>

<style>
  .scan-app-controls {
    display: inline-flex;
    align-items: baseline;
  }
  :global(.scan-app-btn) {
    font-size: 0.8rem;
    padding: 0.3rem 0.65rem;
    min-height: 0;
    line-height: 1.25;
    flex-shrink: 0;
  }
</style>
