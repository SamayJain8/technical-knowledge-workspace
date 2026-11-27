"use strict";
const form = document.querySelector("#ask");
const output = document.querySelector("#response");
const evidence = document.querySelector("#evidence");
const citations = document.querySelector("#citations");
const evidenceCount = document.querySelector("#evidence-count");
const scope = document.querySelector("#scope");
const status = document.querySelector("#status");
const cancel = document.querySelector("#cancel");
let pending;
const library = document.querySelector("#documents");
const uploadStatus = document.querySelector("#upload-status");
const files = document.querySelector("#files");
const dropArea = document.querySelector(".upload-area");
const selected = new Set();
const action = {"X-Library-Action": "1"};

function element(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

function sourceLink(source) {
  try {
    const url = new URL(source.source_url);
    if (url.protocol === "https:" && !url.username && !url.password) {
      const link = element("a", source.title);
      link.href = url.href;
      link.rel = "noopener noreferrer";
      return link;
    }
  } catch { /* Invalid source URLs remain plain text. */ }
  return element("span", source.title);
}

function updateScope() {
  scope.textContent = selected.size ? selected.size + " selected" : "All documents";
}

function filterLibrary() {
  const query = document.querySelector("#library-filter").value.trim().toLowerCase();
  for (const card of library.querySelectorAll(".doc-card")) card.hidden = !card.dataset.title.includes(query);
}

function updateFileSelection() {
  document.querySelector("#file-selection").textContent = files.files.length === 1 ? files.files[0].name :
    (files.files.length ? files.files.length + " files selected" : "");
  document.querySelector("#upload button").disabled = files.disabled || !files.files.length;
}

document.querySelector("#library-filter").addEventListener("input", filterLibrary);
files.addEventListener("change", updateFileSelection);
dropArea.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropArea.classList.add("is-dragging");
});
dropArea.addEventListener("dragleave", () => dropArea.classList.remove("is-dragging"));
dropArea.addEventListener("drop", (event) => {
  event.preventDefault();
  dropArea.classList.remove("is-dragging");
  if (!files.disabled && event.dataTransfer.files.length) {
    files.files = event.dataTransfer.files;
    updateFileSelection();
  }
});

cancel.addEventListener("click", () => pending?.abort());
async function jsonRequest(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed");
  return data;
}

async function refreshLibrary() {
  try {
    const docs = await jsonRequest("/api/v1/documents");
    for (const id of selected) if (!docs.some((doc) => doc.document_id === id)) selected.delete(id);
    updateScope();
    const chunks = docs.reduce((total, doc) => total + doc.chunk_count, 0);
    document.querySelector("#library-stats").textContent = docs.length + " listed documents · " + chunks + " indexed chunks";
    library.replaceChildren();
    if (!docs.length) library.append(element("p", "Upload a document to start your library."));
    for (const doc of docs) {
      const row = element("article", "");
      row.className = "doc-card";
      row.dataset.title = doc.title.toLowerCase();
      const label = element("label", "");
      const pick = element("input", "");
      pick.type = "checkbox";
      pick.checked = selected.has(doc.document_id);
      pick.addEventListener("change", () => {
        if (!pick.checked) selected.delete(doc.document_id);
        else if (selected.size < 16) selected.add(doc.document_id);
        else { pick.checked = false; uploadStatus.textContent = "Select at most 16 documents."; }
        updateScope();
      });
      label.append(pick, document.createTextNode(" " + doc.title));
      const icon = element("span", doc.document_type === "seed" ? "DOC" : doc.document_type.toUpperCase());
      icon.className = "file-icon";
      icon.setAttribute("aria-hidden", "true");
      label.prepend(icon);
      const meta = element("p", doc.chunk_count +
        (doc.chunk_count === 1 ? " chunk" : " chunks") +
        (doc.page_count ? " · " + doc.page_count + " pages" : ""));
      meta.className = "meta";
      row.append(label, meta);
      if (doc.document_type !== "seed") {
        const privacy = element("span", doc.external_ok ? "Gemini approved" : "Gemini blocked");
        privacy.className = "tag";
        const buttons = element("div", "");
        buttons.className = "row-actions";
        const approve = element("button", doc.external_ok ? "Revoke Gemini access" : "Approve public excerpts");
        approve.className = "secondary";
        approve.addEventListener("click", async () => {
          if (!doc.external_ok && !window.confirm("Confirm this document is public and suitable for Gemini free-tier processing.")) return;
          try {
            await jsonRequest("/api/v1/documents/" + doc.document_id + "/eligibility", {
              method: "PATCH", headers: {...action, "Content-Type": "application/json"},
              body: JSON.stringify({approved_public: !doc.external_ok}),
            });
            await refreshLibrary();
          } catch (error) { uploadStatus.textContent = error.message; }
        });
        const remove = element("button", "Delete");
        remove.className = "danger";
        remove.addEventListener("click", async () => {
          if (!window.confirm("Delete this uploaded document and its searchable chunks?")) return;
          try {
            await jsonRequest("/api/v1/documents/" + doc.document_id, {
              method: "DELETE", headers: {...action, "X-Confirm-Delete": doc.document_id},
            });
            await refreshLibrary();
          } catch (error) { uploadStatus.textContent = error.message; }
        });
        buttons.append(approve, remove);
        row.append(privacy, buttons);
      }
      library.append(row);
    }
    filterLibrary();
  } catch (error) {
    document.querySelector("#library-stats").textContent = "Library unavailable";
    uploadStatus.textContent = error.message;
  }
}

document.querySelector("#upload").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const batch = [...files.files];
  button.disabled = true;
  files.disabled = true;
  try {
    for (const file of batch) {
      uploadStatus.textContent = "Uploading " + file.name;
      let job = await jsonRequest("/api/v1/documents?name=" + encodeURIComponent(file.name), {
        method: "POST", headers: {...action, "Content-Type": "application/octet-stream"}, body: file,
      });
      for (let attempt = 0; attempt < 120 && ["queued", "processing"].includes(job.status); attempt++) {
        uploadStatus.textContent = file.name + " · " + job.status;
        await new Promise((resolve) => setTimeout(resolve, 500));
        job = await jsonRequest("/api/v1/ingestion/" + job.job_id);
      }
      if (job.status !== "indexed") throw new Error(job.detail || "Indexing continues. Refresh the library later.");
      uploadStatus.textContent = job.duplicate ? "Already indexed: " + file.name : "Indexed: " + file.name;
      await refreshLibrary();
    }
    files.value = "";
    updateFileSelection();
  } catch (error) { uploadStatus.textContent = error.message; }
  finally { files.disabled = false; updateFileSelection(); }
});

refreshLibrary();
jsonRequest("/health/ready").then(() => {
  const health = document.querySelector("#health");
  health.textContent = "Oracle + MiniLM ready";
  health.dataset.state = "ready";
}).catch(() => {
  const health = document.querySelector("#health");
  health.textContent = "Service not ready";
  health.dataset.state = "error";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (pending) return;
  const operation = event.submitter?.value || "search";
  const mode = operation === "search" ? "search" : "answer";
  const query = document.querySelector("#query").value.trim();
  const permitted = document.querySelector("#public").checked;
  if (!query) { status.textContent = "Enter a question."; return; }
  const body = {query, document_ids: [...selected], strategy: document.querySelector("#strategy").value};
  const kind = document.querySelector("#kind").value;
  if (kind) body.document_type = kind;
  if (mode === "answer") Object.assign(body, {public_question: permitted, mode: operation});
  pending = new AbortController();
  output.replaceChildren();
  citations.replaceChildren();
  evidence.replaceChildren(element("p", "Retrieving source excerpts…"));
  evidenceCount.textContent = "0 results";
  status.textContent = "Searching…";
  status.dataset.state = "loading";
  cancel.disabled = false;
  for (const button of form.querySelectorAll("[type=submit]")) button.disabled = true;
  try {
    const response = await fetch("/api/v1/" + mode, {
      method: "POST", headers: {"Content-Type": "application/json"},
      signal: pending.signal, body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok && !(response.status === 429 && Array.isArray(data.sources))) {
      status.textContent = typeof data.detail === "string" ? data.detail : "Request failed.";
      status.dataset.state = "error";
      evidence.replaceChildren(element("p", "No evidence returned."));
      return;
    }
    const sources = data.sources || data.results || [];
    const reasons = {
      no_matching_evidence: "No matching evidence found.",
      no_eligible_documents: "Matching evidence is available locally. No matching source is approved for Gemini.",
      no_quotable_evidence: "Matching text is available, but no bounded quote could be prepared.",
      question_consent_required: "Approve this public question to send it to Gemini.",
      provider_abstained: "The model abstained because it could not support an answer.",
      provider_not_configured: "Gemini is not configured. Local evidence is available.",
      provider_timeout: "Gemini timed out. Local evidence is available.",
      provider_rate_limited: "Generation is rate limited. Try again shortly.",
      provider_failure: "Gemini is unavailable. Local evidence is available.",
      input_budget: "The evidence exceeds the provider input budget. Try a narrower question.",
      validation_rejected: "The generated citations could not be verified. Local evidence is available.",
      partial_answer: "Some parts could not be answered from the evidence.",
    };
    const message = reasons[data.reason] || {
      insufficient_evidence: "The retrieved evidence could not support an answer.",
      degraded: permitted ? "Generation unavailable. Retrieved evidence is shown below." :
        "Generation needs permission to send a public test question. Retrieved evidence is shown below.",
      ok: mode === "answer" ? "Cited answer ready." : "Search results ready.",
    }[data.status];
    status.textContent = (message || "Request finished.") +
      (Number.isFinite(data.latency_ms) ? " " + Math.round(data.latency_ms) + " ms" : "");
    status.dataset.state = data.reason === "partial_answer" || data.status !== "ok" ? "notice" : "success";
    if (data.answer) {
      output.append(element("h2", "Answer"));
      if (!data.citations?.some((citation) => citation.claim)) output.append(element("p", data.answer));
    }
    if (data.unanswered?.length) {
      const list = document.createElement("ul");
      for (const part of data.unanswered) list.append(element("li", part));
      output.append(element("h2", "Unanswered parts"), list);
    }
    for (const [index, citation] of (data.citations || []).entries()) {
      const chip = element("a", "Citation " + (index + 1));
      chip.href = "#source-citation-" + (index + 1);
      chip.className = "citation-chip";
      if (citation.claim) {
        const claim = element("p", citation.claim + " ");
        claim.append(chip);
        output.append(claim);
      } else {
        output.append(chip);
      }
      const card = element("article", "");
      card.className = "citation-card";
      card.id = "source-citation-" + (index + 1);
      card.tabIndex = -1;
      chip.addEventListener("click", () => card.focus());
      const source = sources.find((row) => row.chunk_id === citation.chunk_id);
      card.append(element("strong", "Citation " + (index + 1)), element("blockquote", citation.quote),
        source ? sourceLink(source) : element("span", citation.document_title));
      if (citation.page_number) card.append(element("span", " · page " + citation.page_number));
      citations.append(card);
    }
    if (data.answer) {
      const copy = element("button", "Copy answer");
      copy.className = "secondary";
      copy.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(data.answer); status.textContent = "Answer copied."; }
        catch { status.textContent = "Clipboard unavailable."; }
      });
      output.append(copy);
    }
    evidenceCount.textContent = sources.length + (sources.length === 1 ? " result" : " results");
    evidence.replaceChildren();
    if (!sources.length) evidence.append(element("p", "No evidence returned."));
    for (const [index, source] of sources.entries()) {
      const details = document.createElement("details");
      details.className = "result-card";
      details.open = index === 0;
      const page = source.page_number ? " · page " + source.page_number : "";
      const fusion = source.fusion_score == null ? "" : " · fusion " + source.fusion_score.toFixed(4);
      const summary = element("summary", (index + 1) + ". " + source.title + page + " ");
      const score = element("span", "Cosine " + source.similarity_score.toFixed(3));
      score.className = "score";
      summary.append(score);
      details.append(summary, element("p", source.text));
      if (fusion) details.append(element("p", fusion.slice(3)));
      details.append(element("p", source.provenance), sourceLink(source));
      evidence.append(details);
    }
  } catch (error) {
    status.textContent = error.name === "AbortError" ? "Request cancelled in this browser." : "Could not reach the service.";
    status.dataset.state = error.name === "AbortError" ? "notice" : "error";
    evidence.replaceChildren(element("p", "No evidence returned."));
  } finally {
    pending = undefined;
    cancel.disabled = true;
    for (const button of form.querySelectorAll("[type=submit]")) button.disabled = false;
  }
});
