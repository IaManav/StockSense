const state = { view: "dashboard", user: null, products: [], categories: [], warehouses: [], locations: [], operations: [], operationLayout: {} };

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;", "'":"&#039;"}[char]));
const pretty = (value) => String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, { credentials: "same-origin", headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function notify(message, type = "success") {
  const node = $("#notice");
  node.textContent = message; node.className = `notice show ${type}`;
  window.clearTimeout(notify.timer); notify.timer = window.setTimeout(() => { node.className = "notice"; }, 4500);
}

function status(value) { return `<span class="status ${String(value || "").toLowerCase()}">${esc(pretty(value || "-"))}</span>`; }
function empty(title, detail = "Nothing has been recorded yet.") { return `<div class="empty"><strong>${esc(title)}</strong><span>${esc(detail)}</span></div>`; }
function table(headers, rows, emptyMessage = "No records found.") {
  return rows.length ? `<div class="table-wrap"><table class="data-table"><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>` : empty(emptyMessage);
}
function optionList(items, labelKey = "name") { return items.map((item) => `<option value="${esc(item.id)}">${esc(item[labelKey])}</option>`).join(""); }

async function loadReferenceData() {
  const [products, categories, warehouses, locations] = await Promise.all([
    api("/products"), api("/categories"), api("/warehouses"), api("/locations")
  ]);
  state.products = products.items || []; state.categories = categories.items || [];
  state.warehouses = warehouses.items || []; state.locations = locations.items || [];
}

function setPageMeta(title) { $("#page-title").textContent = title; $("#breadcrumb").textContent = title; document.title = `StockSense - ${title}`; }
function setActive(view) { document.querySelectorAll(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === view)); }

async function render(view = state.view) {
  state.view = view; setActive(view); const title = view === "ledger" ? "Move history" : view === "products" ? "Stocks" : pretty(view); setPageMeta(title);
  const page = $("#page"); page.innerHTML = `<div class="empty">Loading ${esc(title.toLowerCase())}...</div>`;
  try {
    await loadReferenceData();
    if (view === "dashboard") return renderDashboard();
    if (view === "products") return renderProducts();
    if (view === "stock") return renderStock();
    if (view === "warehouses") return renderWarehouses();
    if (view === "locations") return renderLocations();
    if (view === "ledger") return renderLedger();
    if (["receipts", "deliveries", "transfers", "adjustments"].includes(view)) return renderOperations(view);
    if (view === "profile") return renderProfile();
  } catch (error) { page.innerHTML = `<div class="panel"><div class="panel-body">${empty("Could not load this view", error.message)}</div></div>`; notify(error.message, "error"); }
}

async function renderDashboard() {
  const [receipts, deliveries] = await Promise.all([api("/receipts"), api("/deliveries")]);
  const today = new Date().toISOString().slice(0, 10);
  const active = (item) => !["DONE", "CANCELLED"].includes(item.status);
  const receiptItems = receipts.items || [];
  const deliveryItems = deliveries.items || [];
  const lateReceipts = receiptItems.filter((item) => active(item) && item.schedule_date && item.schedule_date < today);
  const receiptOperations = receiptItems.filter((item) => active(item) && item.schedule_date && item.schedule_date > today);
  const lateDeliveries = deliveryItems.filter((item) => active(item) && item.schedule_date && item.schedule_date < today);
  const waitingDeliveries = deliveryItems.filter((item) => active(item) && item.status === "WAITING");
  const deliveryOperations = deliveryItems.filter((item) => active(item) && item.schedule_date && item.schedule_date > today);
  const operationRows = (items, detailKey) => items.map((item) => `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item[detailKey] || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)}</td></tr>`);
  const subsection = (title, description, counters, items, detailKey, emptyMessage) => `<section class="panel"><div class="panel-head"><div><h2>${title}</h2><span class="muted">${description}</span></div><button class="button button-quiet" data-view="${title.toLowerCase()}">View all →</button></div><div class="panel-body"><div class="cards">${counters.map(([label, value, cls]) => `<div class="mini-card"><span class="muted">${label}</span><strong class="${cls || ""}">${value}</strong></div>`).join("")}</div>${table(["Reference", title === "Receipts" ? "Receive from" : "Delivery address", "Schedule date", "Status"], operationRows(items, detailKey), emptyMessage)}</div></section>`;
  $("#page").innerHTML = `<div class="content-grid"><div class="dashboard-column">${subsection("Receipts", "Incoming stock scheduled for the warehouse", [["Late items", lateReceipts.length, "stock-negative"], ["Operations", receiptOperations.length, ""]], [...lateReceipts, ...receiptOperations], "receive_from", "No receipt operations scheduled.")}</div><div class="dashboard-column">${subsection("Deliveries", "Outgoing stock and customer shipments", [["Late", lateDeliveries.length, "stock-negative"], ["Waiting", waitingDeliveries.length, "warning"], ["Operations", deliveryOperations.length, ""]], [...lateDeliveries, ...waitingDeliveries, ...deliveryOperations], "delivery_address", "No delivery operations scheduled.")}</div></div>`;
}

function renderProducts() {
  const rows = state.products.map((product) => `<tr><td><strong>${esc(product.sku)}</strong></td><td>${esc(product.name)}</td><td>${esc(state.categories.find((item) => item.id === product.category_id)?.name || "Uncategorised")}</td><td>${esc(product.unit || "piece")}</td><td>${esc(product.reorder_level ?? 0)}</td><td>${product.is_active ? status("Ready") : status("Cancelled")}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="toolbar-left"><input class="search" id="product-search" placeholder="Search by name or SKU" value=""></div><div class="toolbar-right"><button class="button button-dark" data-action="new-product">+ New stock item</button></div></div><section class="panel"><div class="panel-head"><div><h2 class="section-title">Stock catalogue</h2><span class="muted">${state.products.length} stock items</span></div><button class="button" data-view="stock">View stock by location</button></div>${table(["SKU","Stock item","Category","Unit","Reorder level","Status"], rows, "No stock items yet. Add the first stock item to begin tracking stock.")}</section>`;
  $("#product-search").addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.textContent.toLowerCase().includes(query); }); });
}

async function renderStock() {
  const result = await api("/stock");
  const rows = (result.items || []).map((item) => {
    const product = state.products.find((entry) => entry.id === item.product_id);
    const location = state.locations.find((entry) => entry.id === item.location_id);
    const available = Number(item.free_to_use || 0);
    return `<tr><td><strong>${esc(product?.sku || item.product_id?.slice(0, 8) || "-")}</strong><br><span class="muted">${esc(product?.name || "Unknown product")}</span></td><td>${esc(location?.name || item.location_id?.slice(0, 8) || "-")}</td><td>${esc(item.on_hand_quantity)}</td><td class="${available <= 0 ? "stock-negative" : "stock-positive"}">${esc(item.free_to_use)}</td><td>${product && Number(product.reorder_level) > available ? status("Waiting") : status("Ready")}</td></tr>`;
  });
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Stock is tracked per product and location. Free to use is on-hand quantity minus reserved quantity.</div><button class="button button-dark" data-action="quick-receipt">+ Receive stock</button></div><section class="panel">${table(["Product","Location","On hand","Free to use","Availability"], rows, "No stock records yet. Validate a receipt or receive stock into a location.")}</section>`;
}

function renderWarehouses() {
  const rows = state.warehouses.map((warehouse) => `<tr><td><strong>${esc(warehouse.name)}</strong></td><td>${esc(warehouse.short_code)}</td><td>${esc(warehouse.address || "-")}</td><td>${state.locations.filter((location) => location.warehouse_id === warehouse.id).length}</td><td>${warehouse.is_active ? status("Ready") : status("Cancelled")}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Warehouses are the top-level stock containers. Add locations such as racks, rooms, or production floors inside each warehouse.</div><button class="button button-dark" data-action="new-warehouse">+ New warehouse</button></div><section class="panel">${table(["Warehouse","Short code","Address","Locations","Status"], rows, "No warehouses configured yet.")}</section>`;
}

function renderLocations() {
  const rows = state.locations.map((location) => `<tr><td><strong>${esc(location.name)}</strong></td><td>${esc(location.short_code)}</td><td>${esc(state.warehouses.find((warehouse) => warehouse.id === location.warehouse_id)?.name || location.warehouse_id?.slice(0, 8) || "-")}</td><td><button class="button button-quiet" data-view="stock">View stock →</button></td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Locations represent racks, rooms, receiving areas, or production floors inside a warehouse.</div><button class="button button-dark" data-action="new-location">+ New location</button></div><section class="panel">${table(["Location","Short code","Warehouse",""], rows, "No locations configured yet.")}</section>`;
}

async function renderLedger() {
  const result = await api("/ledger"); const rows = (result.items || []).map((item) => `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item.product_id?.slice(0, 8) || "-")}</td><td>${esc(item.from_location_id?.slice(0, 8) || "-" )}</td><td>${esc(item.to_location_id?.slice(0, 8) || "-")}</td><td class="${item.move_type === "IN" ? "stock-positive" : "stock-negative"}">${item.move_type === "IN" ? "+" : "-"}${esc(item.quantity)}</td><td>${status(item.move_type)}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Every validated receipt, delivery, transfer, and adjustment is recorded here. Incoming movements are shown in green; outgoing movements in red.</div></div><section class="panel">${table(["Reference","Product","From","To","Quantity","Movement"], rows, "No validated movements yet.")}</section>`;
}

async function renderOperations(view, layout = state.operationLayout[view] || "list") {
  state.operationLayout[view] = layout;
  const labels = { receipts: ["Receipts", "Incoming stock from vendors", "receive_from", "Receive from"], deliveries: ["Deliveries", "Outgoing stock for customer shipments", "delivery_address", "Delivery address"], transfers: ["Internal transfers", "Move stock between warehouse locations", "", ""], adjustments: ["Adjustments", "Reconcile recorded quantities with physical counts", "reason", "Reason"] };
  const [heading, description] = labels[view]; const result = await api(`/${view}`); state.operations = result.items || [];
  const rows = state.operations.map((item) => {
    const nextAction = item.status === "DRAFT" && view !== "adjustments" ? "ready" : item.status === "READY" || (item.status === "DRAFT" && view === "adjustments") ? "validate" : "";
    const actionLabel = nextAction === "ready" ? "Mark ready" : nextAction === "validate" ? "Validate" : "";
    const action = nextAction ? `<button class="button button-quiet" data-op-action="${nextAction}" data-op-type="${view}" data-id="${esc(item.id)}">${actionLabel} →</button>` : `<span class="muted">Complete</span>`;
    if (view === "receipts") {
      const warehouse = state.warehouses.find((entry) => entry.id === item.warehouse_id);
      return `<tr class="receipt-row" data-receipt-id="${esc(item.id)}" data-search="${esc(`${item.reference} ${item.receive_from || ""} ${item.contact || ""}`)}"><td><strong>${esc(item.reference)}</strong></td><td>${esc(item.receive_from || "-")}</td><td>${esc(item.to_location || warehouse?.name || item.warehouse_id?.slice(0, 8) || "-")}</td><td>${esc(item.contact || item.responsible_id?.slice(0, 8) || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)} ${action}</td></tr>`;
    }
    return `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item[labels[view][2]] || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)}</td><td>${action}</td></tr>`;
  });
  const detailColumn = view === "transfers" ? "Route" : view === "adjustments" ? "Reason" : "Address";
  const headers = view === "receipts" ? ["Reference", "From", "To", "Contact", "Schedule date", "Status"] : ["Reference", detailColumn, "Schedule date", "Status", ""];
  const receiptCard = (item) => `<article class="kanban-card"><strong>${esc(item.reference)}</strong><span>${esc(item.receive_from || "-")}</span><span>${esc(item.to_location || "-")}</span><span>${esc(item.contact || "-")}</span><small>${esc(item.schedule_date || "-")}</small>${status(item.status)}</article>`;
  const board = ["DRAFT", "READY", "DONE", "CANCELLED"].map((group) => `<section class="kanban-column"><div class="kanban-column-head">${status(group)}<strong>${state.operations.filter((item) => item.status === group).length}</strong></div>${state.operations.filter((item) => item.status === group).map(receiptCard).join("") || `<div class="muted kanban-empty">No items</div>`}</section>`).join("");
  const content = view === "receipts" && layout === "kanban" ? `<div class="kanban-board">${board}</div>` : table(headers, rows, `No ${heading.toLowerCase()} yet.`);
  const receiptTools = view === "receipts" ? `<input class="search" id="receipt-search" placeholder="Search reference or contact"><button class="button" data-toggle-kanban="receipts">${layout === "kanban" ? "List view" : "Kanban view"}</button>` : "";
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">${heading}</div><div class="muted">${description}</div></div><div class="toolbar-right">${receiptTools}<button class="button button-dark" data-action="new-${view}">+ New ${heading.slice(0, -1).toLowerCase()}</button></div></div><section class="panel">${content}</section>`;
  if (view === "receipts" && layout === "list") $("#receipt-search").addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(query); }); });
}

async function renderReceiptDetail(receiptId) {
  const receipt = await api(`/receipts/${receiptId}`);
  setActive("receipts");
  setPageMeta(`Receipt ${receipt.reference}`);
  const action = receipt.status === "DRAFT" ? `<button class="button button-dark" data-receipt-action="ready" data-id="${esc(receipt.id)}">Todo</button>` : receipt.status === "READY" ? `<button class="button button-dark" data-receipt-action="validate" data-id="${esc(receipt.id)}">Validate</button>` : "";
  const cancel = ["DONE", "CANCELLED"].includes(receipt.status) ? "" : `<button class="button button-danger" data-receipt-action="cancel" data-id="${esc(receipt.id)}">Cancel</button>`;
  const products = (receipt.items || []).map((item) => `<tr><td><strong>${esc(item.sku)}</strong><br><span class="muted">${esc(item.product)}</span></td><td>${esc(item.quantity)}</td></tr>`);
  const statusLabel = receipt.status === "DONE" ? "Received" : pretty(receipt.status);
  $("#page").innerHTML = `<div class="detail-toolbar"><div class="toolbar-left"><button class="button button-quiet" data-view="receipts">← Receipts</button><div><div class="eyebrow">RECEIPT</div><h2 class="detail-title">${esc(receipt.reference)}</h2></div></div><div class="toolbar-right">${action}<button class="button" data-receipt-action="print">Print</button>${cancel}</div></div><div class="detail-layout"><section><div class="panel detail-panel"><div class="detail-status"><span class="muted">Status</span><span class="status ${receipt.status.toLowerCase()}">${statusLabel}</span></div><div class="detail-fields"><div><span>Unique ID</span><strong>${esc(receipt.id)}</strong></div><div><span>Receive from</span><strong>${esc(receipt.receive_from || "-")}</strong></div><div><span>Schedule date</span><strong>${esc(receipt.schedule_date || "-")}</strong></div><div><span>Responsible</span><strong>${esc(receipt.contact || "-")}</strong></div><div><span>To</span><strong>${esc(receipt.to_location || "-")}</strong></div></div></div><section class="panel"><div class="panel-head"><div><h2>Products in receipt</h2><span class="muted">${receipt.items?.length || 0} line(s)</span></div></div>${table(["Product","Quantity"], products, "No products added yet.")}<div class="panel-footer"><button class="button" data-receipt-action="add-product" data-id="${esc(receipt.id)}" ${receipt.status !== "DRAFT" ? "disabled" : ""}>+ New product</button></div></section></section><aside class="panel workflow-panel"><div class="eyebrow">WORKFLOW</div><h3>Receipt status</h3><div class="workflow-step active"><strong>Draft</strong><span>Initial stage</span></div><div class="workflow-step ${["READY", "DONE"].includes(receipt.status) ? "active" : ""}"><strong>Ready</strong><span>Ready to receive</span></div><div class="workflow-step ${receipt.status === "DONE" ? "active" : ""}"><strong>Received</strong><span>Stock updated and receipt closed</span></div></aside></div>`;
}

function openReceiptProductForm(receiptId) {
  formDialog("Add product to receipt", `<label>Stock item<select name="product_id" required><option value="">Select stock item</option>${optionList(state.products)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations)}</select></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`, async (data) => api(`/receipts/${receiptId}/items`, { method: "POST", body: JSON.stringify(Object.fromEntries(data)) }), () => renderReceiptDetail(receiptId));
}

function renderProfile() {
  const user = state.user; $("#page").innerHTML = `<section class="panel"><div class="panel-head"><div><div class="eyebrow">ACCOUNT</div><h2 class="section-title">My profile</h2></div></div><div class="panel-body">${user ? `<div class="cards"><div class="mini-card"><span class="muted">Login ID</span><strong>${esc(user.login_id)}</strong></div><div class="mini-card"><span class="muted">Email</span><strong>${esc(user.email)}</strong></div><div class="mini-card"><span class="muted">Role</span><strong>${esc(user.role)}</strong></div></div>` : `<div class="callout">You are browsing in read-only mode. Sign in to create operations and manage your profile.</div><br><button class="button button-dark" data-action="auth">Sign in</button>`}</div></section>`;
}

function openDialog() { $("#auth-dialog").showModal(); }

function openResetDialog() {
  const dialog = $("#reset-dialog");
  const fields = $(".reset-code-fields");
  fields.classList.remove("active");
  $("#reset-message").textContent = "Request a one-time reset code. It expires after 10 minutes.";
  $("#request-reset").hidden = false;
  $("#complete-reset").hidden = true;
  dialog.showModal();
}

function formDialog(title, content, submit, after = () => render()) { const dialog = document.createElement("dialog"); dialog.className = "modal"; dialog.innerHTML = `<div class="modal-head"><div><div class="eyebrow">NEW RECORD</div><h2>${title}</h2></div><button class="icon-button" data-close-dialog>×</button></div><form class="form-grid">${content}<div class="form-actions"><button type="button" class="button button-quiet" data-close-dialog>Cancel</button><button class="button button-dark">Create</button></div></form>`; document.body.append(dialog); dialog.showModal(); dialog.querySelector("form").addEventListener("submit", async (event) => { event.preventDefault(); try { await submit(new FormData(event.target)); dialog.close(); dialog.remove(); notify(`${title} created`); await after(); } catch (error) { notify(error.message, "error"); } }); dialog.addEventListener("close", () => dialog.remove()); }

function openProductForm() { formDialog("New stock item", `<label>SKU / code<input name="sku" required></label><label>Stock item name<input name="name" required></label><label>Category<select name="category_id"><option value="">Uncategorised</option>${optionList(state.categories)}</select></label><label>Unit of measure<input name="unit" value="piece"></label><label>Unit cost<input name="unit_cost" type="number" min="0" step="0.01" value="0"></label><label>Reorder level<input name="reorder_level" type="number" min="0" step="0.001" value="0"></label><label class="wide">Description<textarea name="description"></textarea></label>`, async (data) => api("/products", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) })); }
function openWarehouseForm() { formDialog("New warehouse", `<label>Warehouse name<input name="name" required></label><label>Short code<input name="short_code" required></label><label class="wide">Address<textarea name="address"></textarea></label>`, async (data) => api("/warehouses", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) })); }
function openLocationForm() { formDialog("New location", `<label>Location name<input name="name" required></label><label>Short code<input name="short_code" required></label><label class="wide">Warehouse<select name="warehouse_id" required><option value="">Select warehouse</option>${optionList(state.warehouses)}</select></label>`, async (data) => api("/locations", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) })); }
function openOperationForm(type) {
  const isReceipt = type === "receipts";
  const isDelivery = type === "deliveries";
  const userId = state.user?.id || "";
  let fields;
  const autoReference = `<div class="wide callout">Reference is generated automatically from the warehouse code and operation type.</div>`;
  const responsibleField = userId ? `<label>Responsible<input value="${esc(state.user.login_id)}" readonly><input type="hidden" name="responsible_id" value="${esc(userId)}"></label>` : `<label>Responsible user ID<input name="responsible_id" placeholder="UUID" required></label>`;
  if (isReceipt || isDelivery) {
    fields = `${autoReference}${responsibleField}<label>Warehouse<select name="warehouse_id" required><option value="">Select warehouse</option>${optionList(state.warehouses)}</select></label><label>Schedule date<input name="schedule_date" type="date"></label><label>${isReceipt ? "Receive from" : "Delivery address"}<input name="${isReceipt ? "receive_from" : "delivery_address"}"></label><label>Stock item<select name="product_id" required><option value="">Select stock item</option>${optionList(state.products)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations)}</select></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`;
  } else if (type === "transfers") {
    fields = `<label>Reference<input name="reference" placeholder="MAIN/MOVE/0001" required></label><label>Responsible user ID<input name="responsible_id" value="${esc(userId)}" placeholder="UUID" required></label><label>From location<select name="from_location_id" required><option value="">Select source</option>${optionList(state.locations)}</select></label><label>To location<select name="to_location_id" required><option value="">Select destination</option>${optionList(state.locations)}</select></label><label>Product<select name="product_id" required><option value="">Select product</option>${optionList(state.products)}</select></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`;
  } else {
    fields = `<label>Reference<input name="reference" placeholder="MAIN/ADJ/0001" required></label><label>Responsible user ID<input name="responsible_id" value="${esc(userId)}" placeholder="UUID" required></label><label>Warehouse<select name="warehouse_id" required><option value="">Select warehouse</option>${optionList(state.warehouses)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations)}</select></label><label>Product<select name="product_id" required><option value="">Select product</option>${optionList(state.products)}</select></label><label>Counted quantity<input name="new_quantity" type="number" min="0" step="0.001" required></label><label class="wide">Reason<input name="reason"></label>`;
  }
  formDialog(`New ${isReceipt ? "receipt" : isDelivery ? "delivery" : type.slice(0, -1)}`, fields, async (data) => {
    const values = Object.fromEntries(data);
    const created = await api(`/${type}`, { method: "POST", body: JSON.stringify(values) });
    if ((isReceipt || isDelivery) && values.product_id) await api(`/${type}/${created.id}/items`, { method: "POST", body: JSON.stringify({ product_id: values.product_id, location_id: values.location_id, quantity: values.quantity }) });
    if (type === "transfers") await api(`/transfers/${created.id}/items`, { method: "POST", body: JSON.stringify({ product_id: values.product_id, quantity: values.quantity }) });
    if (type === "adjustments") await api(`/adjustments/${created.id}/items`, { method: "POST", body: JSON.stringify({ product_id: values.product_id, new_quantity: values.new_quantity }) });
    return created;
  });
}

async function loadUser() { try { state.user = await api("/auth/me"); $("#user-name").textContent = state.user.login_id; $("#user-role").textContent = state.user.role; $("#user-avatar").textContent = state.user.login_id.slice(0, 1).toUpperCase(); $("#connection-status").textContent = "Database connected"; $("#connection-status").className = "connection-dot ok"; } catch { $("#connection-status").textContent = "Read-only mode"; $("#connection-status").className = "connection-dot"; } }

document.addEventListener("click", async (event) => {
  const kanbanToggle = event.target.closest("[data-toggle-kanban]");
  if (kanbanToggle) {
    const view = kanbanToggle.dataset.toggleKanban;
    renderOperations(view, state.operationLayout[view] === "kanban" ? "list" : "kanban");
    return;
  }
  const viewNode = event.target.closest("[data-view]"); if (viewNode) { render(viewNode.dataset.view); $("#sidebar").classList.remove("open"); return; }
  const receiptRow = event.target.closest("[data-receipt-id]");
  if (receiptRow && !event.target.closest("[data-op-action]")) { renderReceiptDetail(receiptRow.dataset.receiptId); return; }
  const receiptAction = event.target.closest("[data-receipt-action]");
  if (receiptAction) {
    const action = receiptAction.dataset.receiptAction;
    const id = receiptAction.dataset.id;
    if (action === "print") { window.print(); return; }
    if (action === "add-product") { await loadReferenceData(); openReceiptProductForm(id); return; }
    try {
      const endpoint = action === "ready" ? `/receipts/${id}/ready` : action === "validate" ? `/receipts/${id}/validate` : `/receipts/${id}/cancel`;
      const options = action === "validate" ? { method: "POST", body: JSON.stringify({ created_by: state.user?.id }) } : { method: "POST" };
      if (action === "validate" && !state.user?.id) throw new Error("Sign in before validating a receipt");
      await api(endpoint, options); notify(action === "ready" ? "Receipt is ready to receive" : action === "validate" ? "Receipt received and stock updated" : "Receipt cancelled"); renderReceiptDetail(id);
    } catch (error) { notify(error.message, "error"); }
    return;
  }
  const operationButton = event.target.closest("[data-op-action]");
  if (operationButton) {
    const { opAction, opType, id } = operationButton.dataset;
    try {
      const endpoint = opAction === "ready" ? `/${opType}/${id}/ready` : `/${opType}/${id}/validate`;
      const body = opAction === "validate" ? { created_by: state.user?.id } : undefined;
      if (opAction === "validate" && !state.user?.id) throw new Error("Sign in before validating an operation");
      await api(endpoint, { method: "POST", ...(body ? { body: JSON.stringify(body) } : {}) });
      notify(opAction === "ready" ? "Operation marked ready" : "Operation validated and stock updated");
      render(opType);
    } catch (error) { notify(error.message, "error"); }
    return;
  }
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "auth") return openDialog();
  if (action === "new-product") return openProductForm();
  if (action === "new-warehouse") return openWarehouseForm();
  if (action === "new-location") return openLocationForm();
  if (action === "quick-receipt") return openOperationForm("receipts");
  if (action?.startsWith("new-")) return openOperationForm(action.slice(4));
  if (event.target.closest("[data-close-dialog]")) return event.target.closest("dialog").close();
  if (event.target.closest("#logout-button")) { try { await api("/auth/logout", { method: "POST" }); state.user = null; loadUser(); render("dashboard"); notify("Signed out"); } catch (error) { notify(error.message, "error"); } }
});

$("#mobile-menu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    state.user = await api("/auth/login", { method: "POST", body: JSON.stringify({ login_id: form.get("login_id"), password: form.get("password") }) });
    $("#auth-dialog").close(); loadUser(); render(); notify("Signed in");
  } catch (error) { notify(error.message, "error"); }
});
$("#signup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    if (form.get("password") !== form.get("confirm_password")) throw new Error("Passwords do not match");
    state.user = await api("/auth/signup", { method: "POST", body: JSON.stringify({ login_id: form.get("login_id"), email: form.get("email"), password: form.get("password") }) });
    $("#auth-dialog").close(); loadUser(); render(); notify("Account created");
  } catch (error) { notify(error.message, "error"); }
});
$("#forgot-password").addEventListener("click", () => { $("#auth-dialog").close(); openResetDialog(); });
$("#request-reset").addEventListener("click", async () => {
  const form = new FormData($("#reset-form"));
  try {
    const result = await api("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email: form.get("email") }) });
    $(".reset-code-fields").classList.add("active"); $("#request-reset").hidden = true; $("#complete-reset").hidden = false;
    $("#reset-message").textContent = result.development_otp ? `Development reset code: ${result.development_otp}` : result.message;
  } catch (error) { notify(error.message, "error"); }
});
$("#reset-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = new FormData(event.target);
  try {
    if (form.get("new_password") !== form.get("confirm_password")) throw new Error("Passwords do not match");
    await api("/auth/reset-password", { method: "POST", body: JSON.stringify({ email: form.get("email"), otp: form.get("otp"), new_password: form.get("new_password") }) });
    $("#reset-dialog").close(); openDialog(); notify("Password reset successful. You can now sign in.");
  } catch (error) { notify(error.message, "error"); }
});
$(".user-chip").addEventListener("click", () => openDialog());

loadUser(); render();
