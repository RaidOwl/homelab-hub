<script>
  import { onMount } from "svelte";

  export let content = "";
  export let onChange = () => {};

  let editorEl;
  let previewEl;
  let richTextEl;
  let mode = "split"; // "edit", "preview", "split"
  let editorType = "markdown"; // "markdown", "richtext"
  let localContent = content;

  // Only update when content changes from outside (document switch)
  $: if (content !== localContent) {
    localContent = content;
    if (richTextEl && editorType === "richtext" && document.activeElement !== richTextEl) {
      richTextEl.innerHTML = renderMarkdown(localContent);
    }
  }

  // Initialize richtext editor when it becomes available
  $: if (richTextEl && editorType === "richtext" && !richTextEl.innerHTML) {
    richTextEl.innerHTML = renderMarkdown(localContent);
  }

  function handleInput(e) {
    localContent = e.target.value;
    onChange(localContent);
  }

  // Convert HTML from rich text editor back to markdown
  function htmlToMarkdown(html) {
    if (!html || html === '<p><br></p>') return '';
    
    let markdown = html
      // Preserve line breaks temporarily
      .replace(/<br\s*\/?>/gi, '\n')
      // Headers
      .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
      .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
      .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
      .replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1\n\n')
      // Bold and italic (handle nested combinations)
      .replace(/<strong[^>]*><em[^>]*>(.*?)<\/em><\/strong>/gi, '***$1***')
      .replace(/<em[^>]*><strong[^>]*>(.*?)<\/strong><\/em>/gi, '***$1***')
      .replace(/<b[^>]*><i[^>]*>(.*?)<\/i><\/b>/gi, '***$1***')
      .replace(/<i[^>]*><b[^>]*>(.*?)<\/b><\/i>/gi, '***$1***')
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
      .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
      .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
      .replace(/<u[^>]*>(.*?)<\/u>/gi, '$1') // Remove underline, not standard markdown
      // Links
      .replace(/<a[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi, '[$2]($1)')
      // Lists - unordered
      .replace(/<ul[^>]*>(.*?)<\/ul>/gis, (match, list) => {
        return list.replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n');
      })
      // Lists - ordered
      .replace(/<ol[^>]*>(.*?)<\/ol>/gis, (match, list) => {
        let counter = 1;
        return list.replace(/<li[^>]*>(.*?)<\/li>/gi, () => `${counter++}. $1\n`);
      })
      // Code blocks
      .replace(/<pre[^>]*><code[^>]*>(.*?)<\/code><\/pre>/gis, '```\n$1\n```\n')
      // Inline code
      .replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`')
      // Blockquotes
      .replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gi, '> $1\n')
      // Paragraphs
      .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
      // Remove any remaining HTML tags
      .replace(/<[^>]+>/g, '')
      // Clean up excessive newlines
      .replace(/\n{3,}/g, '\n\n')
      .trim();
    
    return markdown;
  }

  function handleRichTextInput() {
    if (richTextEl) {
      localContent = htmlToMarkdown(richTextEl.innerHTML);
      onChange(localContent);
    }
  }

  function execCommand(command, value = null) {
    document.execCommand(command, false, value);
    richTextEl?.focus();
  }

  function insertLink() {
    const url = prompt("Enter URL:");
    if (url) {
      execCommand("createLink", url);
    }
  }

  // Simple markdown-to-HTML renderer for preview
  function renderMarkdown(md) {
    if (!md) return "<p></p>";
    let html = md
      // Code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      // Headers
      .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      // Bold & italic
      .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      // Unordered lists
      .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
      // Blockquotes
      .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
      // Horizontal rules
      .replace(/^---$/gm, "<hr>")
      // Line breaks / paragraphs
      .replace(/\n\n/g, "</p><p>")
      .replace(/\n/g, "<br>");
    return `<p>${html}</p>`;
  }
</script>

<div class="editor-container">
  <div class="editor-type-selector">
    <button class:active={editorType === "markdown"} on:click={() => (editorType = "markdown")}>
      Markdown
    </button>
    <button class:active={editorType === "richtext"} on:click={() => (editorType = "richtext")}>
      Rich Text
    </button>
  </div>

  {#if editorType === "markdown"}
    <div class="editor-toolbar">
      <button class:active={mode === "edit"} on:click={() => (mode = "edit")}>Edit</button>
      <button class:active={mode === "split"} on:click={() => (mode = "split")}>Split</button>
      <button class:active={mode === "preview"} on:click={() => (mode = "preview")}>Preview</button>
    </div>

    <div class="editor-panels" class:split={mode === "split"}>
      {#if mode !== "preview"}
        <textarea
          class="editor-textarea"
          bind:this={editorEl}
          value={localContent}
          on:input={handleInput}
          placeholder="Write markdown here..."
          spellcheck="false"
        ></textarea>
      {/if}
      {#if mode !== "edit"}
        <div class="editor-preview" bind:this={previewEl}>
          {@html renderMarkdown(localContent)}
        </div>
      {/if}
    </div>
  {:else}
    <div class="richtext-toolbar">
      <button on:click={() => execCommand('bold')} title="Bold">
        <strong>B</strong>
      </button>
      <button on:click={() => execCommand('italic')} title="Italic">
        <em>I</em>
      </button>
      <button on:click={() => execCommand('underline')} title="Underline">
        <u>U</u>
      </button>
      <span class="separator"></span>
      <button on:click={() => execCommand('formatBlock', '<h1>')} title="Heading 1">
        H1
      </button>
      <button on:click={() => execCommand('formatBlock', '<h2>')} title="Heading 2">
        H2
      </button>
      <button on:click={() => execCommand('formatBlock', '<h3>')} title="Heading 3">
        H3
      </button>
      <button on:click={() => execCommand('formatBlock', '<p>')} title="Paragraph">
        P
      </button>
      <span class="separator"></span>
      <button on:click={() => execCommand('insertUnorderedList')} title="Bullet List">
        • List
      </button>
      <button on:click={() => execCommand('insertOrderedList')} title="Numbered List">
        1. List
      </button>
      <span class="separator"></span>
      <button on:click={insertLink} title="Insert Link">
        Link
      </button>
      <button on:click={() => execCommand('removeFormat')} title="Clear Formatting">
        Clear
      </button>
    </div>

    <div
      class="richtext-editor"
      bind:this={richTextEl}
      contenteditable="true"
      on:input={handleRichTextInput}
      on:blur={handleRichTextInput}
    ></div>
  {/if}
</div>

<style>
  .editor-container {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
  }
  .editor-type-selector {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background: var(--pico-card-background-color, #1e1e2e);
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
  }
  .editor-type-selector button {
    padding: 0.35rem 1rem;
    font-size: 0.85rem;
    margin: 0;
    background: var(--pico-secondary-background, #2e2e3e);
    border: 1px solid var(--pico-muted-border-color, #333);
    color: #ffffff;
    cursor: pointer;
    border-radius: 4px;
  }
  .editor-type-selector button.active {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.15));
    color: var(--pico-primary, #6366f1);
    border-color: var(--pico-primary, #6366f1);
  }
  .editor-toolbar {
    display: flex;
    gap: 0;
    padding: 0.25rem 0.5rem;
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
  }
  .editor-toolbar button {
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    margin: 0;
    background: none;
    border: 1px solid var(--pico-muted-border-color, #333);
    color: #ffffff;
    cursor: pointer;
  }
  .editor-toolbar button.active {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.15));
    color: var(--pico-primary, #6366f1);
  }
  .editor-panels {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  .editor-panels.split {
    gap: 1px;
  }
  .editor-textarea {
    flex: 1;
    resize: none;
    border: none;
    border-radius: 0;
    padding: 1rem;
    font-family: monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    margin: 0;
  }
  .editor-preview {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    border-left: 1px solid var(--pico-muted-border-color, #333);
  }
  .editor-preview :global(pre) {
    background: var(--pico-card-background-color, #1e1e2e);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }
  .editor-preview :global(code) {
    font-size: 0.85rem;
  }
  .richtext-toolbar {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    border-bottom: 1px solid var(--pico-muted-border-color, #333);
    flex-wrap: wrap;
    align-items: center;
  }
  .richtext-toolbar button {
    padding: 0.35rem 0.6rem;
    font-size: 0.8rem;
    margin: 0;
    background: var(--pico-secondary-background, #2e2e3e);
    border: 1px solid var(--pico-muted-border-color, #333);
    color: #ffffff;
    cursor: pointer;
    border-radius: 3px;
    min-width: 2rem;
  }
  .richtext-toolbar button:hover {
    background: var(--pico-primary-background, rgba(99, 102, 241, 0.15));
    color: var(--pico-primary, #6366f1);
  }
  .richtext-toolbar .separator {
    width: 1px;
    height: 1.5rem;
    background: var(--pico-muted-border-color, #333);
    margin: 0 0.25rem;
  }
  .richtext-editor {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    outline: none;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 0.95rem;
    line-height: 1.6;
    direction: ltr;
    unicode-bidi: embed;
    text-align: left;
    color: #ffffff;
  }
  .richtext-editor :global(h1),
  .richtext-editor :global(h2),
  .richtext-editor :global(h3),
  .richtext-editor :global(p),
  .richtext-editor :global(li) {
    color: #ffffff;
  }
  .richtext-editor :global(h1) {
    font-size: 2rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .richtext-editor :global(h2) {
    font-size: 1.5rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .richtext-editor :global(h3) {
    font-size: 1.25rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .richtext-editor :global(p) {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .richtext-editor :global(ul),
  .richtext-editor :global(ol) {
    margin-left: 1.5rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .richtext-editor :global(a) {
    color: var(--pico-primary, #6366f1);
    text-decoration: underline;
  }
</style>
