<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import TreeNode from "./TreeNode.svelte";

  let treeData = [];
  let loading = true;
  let expandedNodes = new Set();
  let selectedNode = null;
  let selectedNodeDetails = null;
  let loadingDetails = false;

  onMount(async () => {
    await loadTreeData();
  });

  async function loadTreeData() {
    loading = true;
    try {
      const graphRes = await get("/map/graph");
      const nodes = graphRes.nodes || [];
      const edges = graphRes.edges || [];
      
      // Build adjacency map
      const childrenMap = new Map();
      edges.forEach(edge => {
        const parentId = edge.data.source;
        const childId = edge.data.target;
        if (!childrenMap.has(parentId)) {
          childrenMap.set(parentId, []);
        }
        childrenMap.get(parentId).push(childId);
      });

      // Find root nodes (rank 0)
      const rootNodes = nodes.filter(n => n.data.rank === 0);
      
      // Build tree structure
      function buildTreeNode(nodeData) {
        const node = nodes.find(n => n.data.id === nodeData.data.id);
        const childIds = childrenMap.get(node.data.id) || [];
        const children = childIds.map(childId => {
          const childNode = nodes.find(n => n.data.id === childId);
          return buildTreeNode(childNode);
        });
        
        return {
          id: node.data.id,
          label: node.data.rawName || node.data.label,
          type: node.data.type,
          icon: node.data.icon,
          imageIcon: node.data.imageIcon,
          networkColor: node.data.networkColor,
          networkName: node.data.networkName,
          entity_id: node.data.entity_id,
          children
        };
      }

      treeData = rootNodes.map(buildTreeNode);
    } catch (e) {
      console.error('Failed to load tree data:', e);
    }
    loading = false;
  }

  function toggleNode(nodeId) {
    if (expandedNodes.has(nodeId)) {
      expandedNodes.delete(nodeId);
    } else {
      expandedNodes.add(nodeId);
    }
    expandedNodes = expandedNodes; // Trigger reactivity
  }

  function expandAll() {
    function collectIds(nodes) {
      const ids = [];
      nodes.forEach(node => {
        ids.push(node.id);
        if (node.children && node.children.length > 0) {
          ids.push(...collectIds(node.children));
        }
      });
      return ids;
    }
    expandedNodes = new Set(collectIds(treeData));
  }

  function collapseAll() {
    expandedNodes = new Set();
  }
  
  async function loadNodeDetails(node) {
    if (!node) return;
    loadingDetails = true;
    try {
      const response = await get(`/${node.type}/${node.entity_id}`);
      selectedNodeDetails = response.data;
    } catch (e) {
      console.error('Failed to load node details:', e);
      selectedNodeDetails = null;
    }
    loadingDetails = false;
  }
  
  function handleNodeClick(event) {
    selectedNode = event.detail;
    loadNodeDetails(selectedNode);
  }
  
  $: if (!selectedNode) {
    selectedNodeDetails = null;
    loadingDetails = false;
  }
</script>

<div class="tree-view">
  {#if loading}
    <div class="loading">Loading tree...</div>
  {:else}
    <div class="tree-controls">
      <button class="outline secondary small" on:click={expandAll}>Expand All</button>
      <button class="outline secondary small" on:click={collapseAll}>Collapse All</button>
    </div>
    
    <div class="tree-container">
      {#each treeData as rootNode}
        <TreeNode 
          node={rootNode} 
          bind:expandedNodes 
          {selectedNode}
          on:toggle={(e) => toggleNode(e.detail)} 
          on:nodeclick={handleNodeClick}
          level={0} 
        />
      {/each}
    </div>
    
    {#if selectedNode}
      <div class="info-panel">
        <div class="info-header">
          <h3>
            {#if selectedNode.icon}
              <span class="node-icon">{selectedNode.icon}</span>
            {/if}
            {selectedNode.label}
          </h3>
          <button class="close-btn" on:click={() => selectedNode = null}>×</button>
        </div>
        <div class="info-content">
          <div class="info-item">
            <span class="info-label">Type:</span>
            <span class="info-value">{selectedNode.type}</span>
          </div>
          {#if loadingDetails}
            <div class="info-item">
              <span class="info-label">Loading...</span>
            </div>
          {:else if selectedNodeDetails}
            {#if selectedNodeDetails.hostname}
              <div class="info-item">
                <span class="info-label">Hostname:</span>
                <span class="info-value">{selectedNodeDetails.hostname}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.ip_address || selectedNodeDetails.ip}
              <div class="info-item">
                <span class="info-label">IP Address:</span>
                <span class="info-value">{selectedNodeDetails.ip_address || selectedNodeDetails.ip}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.mac_address}
              <div class="info-item">
                <span class="info-label">MAC Address:</span>
                <span class="info-value">{selectedNodeDetails.mac_address}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.os}
              <div class="info-item">
                <span class="info-label">OS:</span>
                <span class="info-value">{selectedNodeDetails.os}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.cpu}
              <div class="info-item">
                <span class="info-label">CPU:</span>
                <span class="info-value">{selectedNodeDetails.cpu}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.cpu_cores}
              <div class="info-item">
                <span class="info-label">CPU Cores:</span>
                <span class="info-value">{selectedNodeDetails.cpu_cores}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.ram_gb}
              <div class="info-item">
                <span class="info-label">RAM:</span>
                <span class="info-value">{selectedNodeDetails.ram_gb} GB</span>
              </div>
            {/if}
            {#if selectedNodeDetails.port}
              <div class="info-item">
                <span class="info-label">Port:</span>
                <span class="info-value">{selectedNodeDetails.port}</span>
              </div>
            {/if}
            {#if selectedNode.type === 'apps' && selectedNodeDetails.port && (selectedNodeDetails.hostname || selectedNodeDetails.ip_address)}
              <div class="info-item">
                <span class="info-label">Link:</span>
                <span class="info-value">
                  <a href="{selectedNodeDetails.https ? 'https' : 'http'}://{selectedNodeDetails.hostname || selectedNodeDetails.ip_address}:{selectedNodeDetails.port}" target="_blank" rel="noopener noreferrer">
                    {selectedNodeDetails.hostname || selectedNodeDetails.ip_address}:{selectedNodeDetails.port}
                  </a>
                </span>
              </div>
            {/if}
            {#if selectedNodeDetails.external_hostname}
              <div class="info-item">
                <span class="info-label">External Host:</span>
                <span class="info-value">{selectedNodeDetails.external_hostname}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.storage_type}
              <div class="info-item">
                <span class="info-label">Storage Type:</span>
                <span class="info-value">{selectedNodeDetails.storage_type}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.raid_type}
              <div class="info-item">
                <span class="info-label">RAID:</span>
                <span class="info-value">{selectedNodeDetails.raid_type}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.raw_space_tb}
              <div class="info-item">
                <span class="info-label">Raw Space:</span>
                <span class="info-value">{selectedNodeDetails.raw_space_tb} TB</span>
              </div>
            {/if}
            {#if selectedNodeDetails.usable_space_tb}
              <div class="info-item">
                <span class="info-label">Usable Space:</span>
                <span class="info-value">{selectedNodeDetails.usable_space_tb} TB</span>
              </div>
            {/if}
            {#if selectedNodeDetails.filesystem}
              <div class="info-item">
                <span class="info-label">Filesystem:</span>
                <span class="info-value">{selectedNodeDetails.filesystem}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.category}
              <div class="info-item">
                <span class="info-label">Category:</span>
                <span class="info-value">{selectedNodeDetails.category}</span>
              </div>
            {/if}
            {#if selectedNodeDetails.description}
              <div class="info-item">
                <span class="info-label">Description:</span>
                <span class="info-value">{selectedNodeDetails.description}</span>
              </div>
            {/if}
          {/if}
          {#if selectedNode.networkName}
            <div class="info-item">
              <span class="info-label">Network:</span>
              <span class="info-value">
                <span class="network-indicator" style="background-color: {selectedNode.networkColor}"></span>
                {selectedNode.networkName}
              </span>
            </div>
          {/if}
          {#if selectedNodeDetails && selectedNodeDetails.share_type}
            <div class="info-item">
              <span class="info-label">Share Type:</span>
              <span class="info-value">{selectedNodeDetails.share_type}</span>
            </div>
          {/if}
          {#if selectedNodeDetails && selectedNodeDetails.notes}
            <div class="info-item notes">
              <span class="info-label">Notes:</span>
              <span class="info-value">{selectedNodeDetails.notes}</span>
            </div>
          {/if}
        </div>
        <div class="info-footer">
          <a href="#/inventory/{selectedNode.type}" class="view-link">View in Inventory →</a>
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .tree-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--pico-background-color, #1a1a1a);
  }
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--pico-muted-color, #999);
  }
  
  .tree-controls {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem;
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
  }
  
  .tree-controls button {
    margin: 0;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
  }
  
  .tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .info-panel {
    position: fixed;
    top: 200px;
    right: 20px;
    width: 320px;
    background: var(--pico-card-background-color, #1e1e2e);
    border: 1px solid var(--pico-muted-border-color, #333);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    max-height: calc(100vh - 240px);
    display: flex;
    flex-direction: column;
  }
  
  .info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
  }
  
  .info-header h3 {
    margin: 0;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .node-icon {
    font-size: 1.3rem;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: var(--pico-muted-color, #999);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0;
  }
  
  .close-btn:hover {
    color: var(--pico-primary, #6366f1);
  }
  
  .info-content {
    padding: 1rem;
    overflow-y: auto;
    flex: 1;
  }
  
  .info-item {
    display: flex;
    flex-direction: column;
    margin-bottom: 0.75rem;
  }
  
  .info-item.notes {
    margin-top: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--pico-muted-border-color, #333);
  }
  
  .info-label {
    font-size: 0.75rem;
    color: var(--pico-muted-color, #999);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
  }
  
  .info-value {
    font-size: 0.9rem;
    color: #ffffff;
    word-break: break-word;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .network-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
  }
  
  .info-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--pico-muted-border-color, #333);
    background: rgba(0, 0, 0, 0.2);
  }
  
  .view-link {
    color: var(--pico-primary, #6366f1);
    text-decoration: none;
    font-size: 0.85rem;
    display: inline-block;
  }
  
  .view-link:hover {
    text-decoration: underline;
  }
</style>
