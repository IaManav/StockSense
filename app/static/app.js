const state = { view: "dashboard", user: null, products: [], categories: [], warehouses: [], locations: [], operations: [], operationLayout: {}, currentWarehouseId: localStorage.getItem("stocksense.currentWarehouseId"), currentLocationId: localStorage.getItem("stocksense.currentLocationId") };

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;", "'":"&#039;"}[char]));
const pretty = (value) => String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, { credentials: "same-origin", cache: options.method && options.method.toUpperCase() !== "GET" ? "default" : "no-store", headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function notify(message, type = "success") {
  const node = $("#notice");
  node.textContent = message; node.className = `notice show ${type}`;
  window.clearTimeout(notify.timer); notify.timer = window.setTimeout(() => { node.className = "notice"; }, 4500);
}

function showAuthMessage(id, message, type = "error") { const node = $("#" + id); if (!node) return; node.textContent = message; node.className = "auth-message show " + type; node.style.color = type === "success" ? "var(--green)" : ""; node.style.borderColor = type === "success" ? "#c8e6d5" : ""; node.style.background = type === "success" ? "#f7fffa" : ""; }

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
  if (!state.warehouses.some((warehouse) => warehouse.id === state.currentWarehouseId)) state.currentWarehouseId = state.warehouses[0]?.id || null;
  const locationsInWarehouse = state.locations.filter((location) => location.warehouse_id === state.currentWarehouseId);
  if (!locationsInWarehouse.some((location) => location.id === state.currentLocationId)) state.currentLocationId = locationsInWarehouse[0]?.id || null;
  localStorage.setItem("stocksense.currentWarehouseId", state.currentWarehouseId || "");
  localStorage.setItem("stocksense.currentLocationId", state.currentLocationId || "");
}

function currentContextControls() {
  const locations = state.locations.filter((location) => location.warehouse_id === state.currentWarehouseId);
  return `<div class="toolbar-right"><select class="select" id="current-warehouse" aria-label="Current warehouse">${state.warehouses.map((warehouse) => `<option value="${esc(warehouse.id)}" ${warehouse.id === state.currentWarehouseId ? "selected" : ""}>${esc(warehouse.name)}</option>`).join("")}</select><select class="select" id="current-location" aria-label="Current location"><option value="">All locations</option>${locations.map((location) => `<option value="${esc(location.id)}" ${location.id === state.currentLocationId ? "selected" : ""}>${esc(location.name)}</option>`).join("")}</select></div>`;
}

function bindCurrentContextControls() {
  $("#current-warehouse")?.addEventListener("change", (event) => { state.currentWarehouseId = event.target.value; state.currentLocationId = state.locations.find((location) => location.warehouse_id === state.currentWarehouseId)?.id || null; localStorage.setItem("stocksense.currentWarehouseId", state.currentWarehouseId || ""); localStorage.setItem("stocksense.currentLocationId", state.currentLocationId || ""); render(state.view); });
  $("#current-location")?.addEventListener("change", (event) => { state.currentLocationId = event.target.value || null; localStorage.setItem("stocksense.currentLocationId", state.currentLocationId || ""); render(state.view); });
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

async function renderProducts() {
  const result = await api("/stock");
  const rows = (result.items || []).map((item) => {
    const product = state.products.find((entry) => entry.id === item.product_id);
    const location = state.locations.find((entry) => entry.id === item.location_id);
    const warehouse = state.warehouses.find((entry) => entry.id === location?.warehouse_id);
    const available = Number(item.free_to_use || 0);
    const updateControl = item.location_id ? `<button class="button button-quiet" data-stock-update="true" data-product-id="${esc(item.product_id)}" data-location-id="${esc(item.location_id)}" data-product-name="${esc(product?.name || "Stock item")}" data-location-name="${esc(`${warehouse?.name || "Warehouse"} / ${location?.name || "Location"}`)}" data-on-hand="${esc(item.on_hand_quantity)}">Update</button>` : `<span class="muted">No balance</span>`;
    return `<tr data-search="${esc(`${product?.sku || ""} ${product?.name || ""} ${warehouse?.name || ""} ${location?.name || ""}`)}"><td><strong>${esc(product?.name || "Unknown product")}</strong><br><span class="muted">${esc(product?.sku || item.product_id?.slice(0, 8) || "-")}</span><br><small class="muted">${esc(warehouse?.name || "No warehouse")} / ${esc(location?.name || "No location")}</small></td><td>${esc(product?.unit_cost ?? 0)}</td><td>${esc(item.on_hand_quantity)} ${updateControl}</td><td class="${available <= 0 ? "stock-negative" : "stock-positive"}">${esc(item.free_to_use)}</td></tr>`;
  });
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">Stock catalogue</div><div class="muted">Inventory balances by warehouse and location</div></div><div class="toolbar-right"><input class="search" id="product-search" placeholder="Search product, warehouse, or location"><button class="button" data-action="quick-stock">+ Add stock</button><button class="button button-dark" data-action="new-product">+ New stock item</button></div></div><section class="panel"><div class="panel-head"><div><h2>Stock catalogue</h2><span class="muted">${rows.length} stock balance(s)</span></div></div>${table(["Product", "Per unit cost", "On hand (units)", "Free to use (units)"], rows, "No stock records yet. Add stock or validate a receipt to begin tracking inventory.")}</section>`;
  $("#product-search").addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(query); }); });
}

async function renderStock() {
  const result = await api("/stock");
  const rows = (result.items || []).map((item) => {
    const product = state.products.find((entry) => entry.id === item.product_id);
    const location = state.locations.find((entry) => entry.id === item.location_id);
    const warehouse = state.warehouses.find((entry) => entry.id === location?.warehouse_id);
    const available = Number(item.free_to_use || 0);
    const updateControl = item.location_id ? `<button class="button button-quiet" data-stock-update="true" data-product-id="${esc(item.product_id)}" data-location-id="${esc(item.location_id)}" data-product-name="${esc(product?.name || "Stock item")}" data-location-name="${esc(`${warehouse?.name || "Warehouse"} / ${location?.name || "Location"}`)}" data-on-hand="${esc(item.on_hand_quantity)}">Update</button>` : `<span class="muted">No balance</span>`;
    return `<tr data-search="${esc(`${product?.sku || ""} ${product?.name || ""} ${warehouse?.name || ""} ${location?.name || ""}`)}"><td><strong>${esc(product?.name || "Unknown product")}</strong><br><span class="muted">${esc(product?.sku || item.product_id?.slice(0, 8) || "-")}</span><br><small class="muted">${esc(warehouse?.name || "No warehouse")} / ${esc(location?.name || "No location")}</small></td><td>${esc(product?.unit_cost ?? 0)}</td><td>${esc(item.on_hand_quantity)} ${updateControl}</td><td class="${available <= 0 ? "stock-negative" : "stock-positive"}">${esc(item.free_to_use)}</td></tr>`;
  });
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">Stock</div><div class="muted">Inventory balances by warehouse and location</div></div><div class="toolbar-right"><input class="search" id="stock-search" placeholder="Search product, warehouse, or location"><button class="button button-dark" data-action="quick-stock">+ Add stock</button></div></div><section class="panel"><div class="panel-head"><div><h2>Stock by location</h2><span class="muted">Free to use is on-hand quantity minus reserved quantity.</span></div></div>${table(["Product", "Per unit cost", "On hand (units)", "Free to use (units)"], rows, "No stock records yet. Add stock or validate a receipt to begin tracking inventory.")}</section>`;
  $("#stock-search").addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(query); }); });
}

function openStockUpdateForm(button) {
  const { productId, locationId, productName, locationName, onHand } = button.dataset;
  formDialog("Update stock", `<div class="callout wide">${esc(productName)}<br><span class="muted">${esc(locationName)}</span></div><label class="wide">On-hand quantity<input name="on_hand_quantity" type="number" min="0" step="0.001" value="${esc(onHand)}" required></label>`, async (data) => api(`/stock/${productId}/${locationId}`, { method: "PUT", body: JSON.stringify(Object.fromEntries(data)) }), async () => { await (state.view === "products" ? renderProducts() : renderStock()); });
}

function openStockReceiveForm() {
  formDialog("Add stock", `<label>Stock item<select name="product_id" required><option value="">Select stock item</option>${optionList(state.products)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations.filter((location) => location.warehouse_id === state.currentWarehouseId))}</select></label><label class="wide">Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`, async (data) => { const values = Object.fromEntries(data); return api(`/stock/${values.product_id}/${values.location_id}/receive`, { method: "POST", body: JSON.stringify({ quantity: values.quantity }) }); }, async () => { await (state.view === "products" ? renderProducts() : renderStock()); });
}

function renderWarehouses() {
  const rows = state.warehouses.map((warehouse) => `<tr><td><strong>${esc(warehouse.name)}</strong>${warehouse.id === state.currentWarehouseId ? ` <span class="status ready">Current</span>` : ""}</td><td>${esc(warehouse.short_code)}</td><td>${esc(warehouse.address || "-")}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Current warehouse: <strong>${esc(state.warehouses.find((warehouse) => warehouse.id === state.currentWarehouseId)?.name || "Not selected")}</strong></div>${currentContextControls()}<button class="button button-dark" data-action="new-warehouse">+ New warehouse</button></div><section class="panel">${table(["Name", "Shortcut code", "Address"], rows, "No warehouses configured yet.")}</section>`;
  bindCurrentContextControls();
}

function renderLocations() {
  const rows = state.locations.filter((location) => location.warehouse_id === state.currentWarehouseId).map((location) => `<tr><td><strong>${esc(location.name)}</strong>${location.id === state.currentLocationId ? ` <span class="status ready">Current</span>` : ""}</td><td>${esc(location.short_code)}</td><td>${esc(state.warehouses.find((warehouse) => warehouse.id === location.warehouse_id)?.name || location.warehouse_id?.slice(0, 8) || "-")}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Current warehouse: <strong>${esc(state.warehouses.find((warehouse) => warehouse.id === state.currentWarehouseId)?.name || "Not selected")}</strong>${state.currentLocationId ? ` · Current location: <strong>${esc(state.locations.find((location) => location.id === state.currentLocationId)?.name || "Not selected")}</strong>` : ""}</div>${currentContextControls()}<button class="button button-dark" data-action="new-location">+ New location</button></div><section class="panel">${table(["Name", "Shortcut code", "Warehouse"], rows, "No locations configured for the current warehouse.")}</section>`;
  bindCurrentContextControls();
}

async function renderLedger() {
  const layout = state.operationLayout.ledger || "list";
  state.operationLayout.ledger = layout;
  const result = await api("/ledger");
  const movements = result.items || [];
  const movementType = (item) => item.status || item.move_type;
  const displayDate = (item) => item.date ? new Date(item.date).toLocaleDateString() : "-";
  const rows = movements.map((item) => `<tr data-search="${esc(`${item.reference} ${item.contact || ""}`)}"><td><strong>${esc(item.reference)}</strong></td><td>${esc(displayDate(item))}</td><td>${esc(item.contact || "-")}</td><td>${esc(item.from || "-")}</td><td>${esc(item.to || "-")}</td><td class="${item.move_type === "IN" ? "stock-positive" : item.move_type === "OUT" ? "stock-negative" : ""}">${item.move_type === "IN" ? "+" : item.move_type === "OUT" ? "-" : ""}${esc(item.quantity)}</td><td>${status(movementType(item))}</td></tr>`);
  const groups = ["IN", "OUT", "TRANSFER", "ADJUSTMENT"];
  const card = (item) => `<article class="kanban-card"><strong>${esc(item.reference)}</strong><span>${esc(item.contact || "-")}</span><span>${esc(item.from || "-")} → ${esc(item.to || "-")}</span><small>${esc(displayDate(item))} · ${esc(item.quantity)}</small>${status(movementType(item))}</article>`;
  const board = groups.map((group) => `<section class="kanban-column"><div class="kanban-column-head">${status(group)}<strong>${movements.filter((item) => movementType(item) === group).length}</strong></div>${movements.filter((item) => movementType(item) === group).map(card).join("") || `<div class="muted kanban-empty">No items</div>`}</section>`).join("");
  const content = layout === "kanban" ? `<div class="kanban-board">${board}</div>` : table(["Reference", "Date", "Contact", "From", "To", "Quantity", "Status"], rows, "No validated movements yet.");
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">Move history</div><div class="muted">Every stock movement recorded by the system</div></div><div class="toolbar-right"><input class="search" id="ledger-search" placeholder="Search reference or contact"><button class="button" data-toggle-kanban="ledger">${layout === "kanban" ? "List view" : "Kanban view"}</button></div></div><section class="panel">${content}</section>`;
  if (layout === "list") $("#ledger-search").addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(query); }); });
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
    if (view === "deliveries") {
      return `<tr class="delivery-row" data-delivery-id="${esc(item.id)}" data-search="${esc(`${item.reference} ${item.contact || ""} ${item.from_warehouse || ""} ${item.to_address || ""}`)}"><td><strong>${esc(item.reference)}</strong></td><td>${esc(item.from_warehouse || "-")}</td><td>${esc(item.to_address || "-")}</td><td>${esc(item.contact || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)} ${action}</td></tr>`;
    }
    return `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item[labels[view][2]] || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)}</td><td>${action}</td></tr>`;
  });
  const detailColumn = view === "transfers" ? "Route" : view === "adjustments" ? "Reason" : "Address";
  const headers = ["receipts", "deliveries"].includes(view) ? ["Reference", "From", "To", "Contact", "Schedule date", "Status"] : ["Reference", detailColumn, "Schedule date", "Status", ""];
  const operationCard = (item) => {
    const fields = view === "receipts" ? [item.receive_from, item.to_location, item.contact] : [item.from_warehouse, item.to_address, item.contact];
    return `<article class="kanban-card"><strong>${esc(item.reference)}</strong>${fields.map((field) => `<span>${esc(field || "-")}</span>`).join("")}<small>${esc(item.schedule_date || "-")}</small>${status(item.status)}</article>`;
  };
  const boardGroups = view === "deliveries" ? ["DRAFT", "WAITING", "READY", "DONE", "CANCELLED"] : ["DRAFT", "READY", "DONE", "CANCELLED"];
  const board = boardGroups.map((group) => `<section class="kanban-column"><div class="kanban-column-head">${status(group)}<strong>${state.operations.filter((item) => item.status === group).length}</strong></div>${state.operations.filter((item) => item.status === group).map(operationCard).join("") || `<div class="muted kanban-empty">No items</div>`}</section>`).join("");
  const kanbanEnabled = ["receipts", "deliveries"].includes(view) && layout === "kanban";
  const content = kanbanEnabled ? `<div class="kanban-board">${board}</div>` : table(headers, rows, `No ${heading.toLowerCase()} yet.`);
  const operationTools = view === "receipts" || view === "deliveries" ? `<input class="search" id="${view === "receipts" ? "receipt" : "delivery"}-search" placeholder="Search reference or contact"><button class="button" data-toggle-kanban="${view}">${layout === "kanban" ? "List view" : "Kanban view"}</button>` : "";
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">${heading}</div><div class="muted">${description}</div></div><div class="toolbar-right">${operationTools}<button class="button button-dark" data-action="new-${view}">+ New ${heading.slice(0, -1).toLowerCase()}</button></div></div><section class="panel">${content}</section>`;
  if ((view === "receipts" || view === "deliveries") && layout === "list") { const search = $(`#${view === "receipts" ? "receipt" : "delivery"}-search`); search.addEventListener("input", (event) => { const query = event.target.value.toLowerCase(); document.querySelectorAll(".data-table tbody tr").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(query); }); }); }
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

async function renderDeliveryDetail(deliveryId) {
  const delivery = await api(`/deliveries/${deliveryId}`);
  setActive("deliveries");
  setPageMeta(`Delivery ${delivery.reference}`);
  const shortages = (delivery.items || []).filter((item) => item.insufficient_stock);
  const action = delivery.status === "DRAFT" ? `<button class="button button-dark" data-delivery-action="ready" data-id="${esc(delivery.id)}">Todo</button>` : delivery.status === "WAITING" ? `<button class="button button-dark" data-delivery-action="ready" data-id="${esc(delivery.id)}">Check stock</button>` : delivery.status === "READY" ? `<button class="button button-dark" data-delivery-action="validate" data-id="${esc(delivery.id)}">Validate</button>` : "";
  const cancel = ["DONE", "CANCELLED"].includes(delivery.status) ? "" : `<button class="button button-danger" data-delivery-action="cancel" data-id="${esc(delivery.id)}">Cancel</button>`;
  const products = (delivery.items || []).map((item) => `<tr><td><strong>${esc(item.sku)}</strong><br><span class="muted">${esc(item.product)}</span></td><td class="${item.insufficient_stock ? "stock-negative" : ""}" title="Available: ${esc(item.available_quantity)}">${esc(item.quantity)}${item.insufficient_stock ? " <span aria-label=\"Insufficient stock\">⚠</span>" : ""}</td></tr>`);
  const statusLabel = pretty(delivery.status);
  const warning = shortages.length ? `<div class="callout" style="border-left-color:var(--red);color:var(--red);background:#fff8f8">${shortages.length} product line(s) exceed available stock. Delivery is waiting for stock.</div>` : "";
  $("#page").innerHTML = `<div class="detail-toolbar"><div class="toolbar-left"><button class="button button-quiet" data-view="deliveries">← Deliveries</button><div><div class="eyebrow">DELIVERY</div><h2 class="detail-title">${esc(delivery.reference)}</h2></div></div><div class="toolbar-right">${action}<button class="button" data-delivery-action="print">Print</button>${cancel}</div></div><div class="detail-layout"><section>${warning}<div class="panel detail-panel"><div class="detail-status"><span class="muted">Status</span><span class="status ${delivery.status.toLowerCase()}">${statusLabel}</span></div><div class="detail-fields"><div><span>Unique ID</span><strong>${esc(delivery.id)}</strong></div><div><span>Delivery address</span><strong>${esc(delivery.delivery_address || "-")}</strong></div><div><span>Schedule date</span><strong>${esc(delivery.schedule_date || "-")}</strong></div><div><span>Responsible</span><strong>${esc(delivery.contact || "-")}</strong></div><div><span>Operation</span><strong>${esc(delivery.operation_type || "Delivery")}</strong></div><div><span>From</span><strong>${esc(delivery.from_warehouse || "-")}</strong></div></div></div><section class="panel"><div class="panel-head"><div><h2>Products in delivery</h2><span class="muted">${delivery.items?.length || 0} line(s)</span></div></div>${table(["Product", "Quantity"], products, "No products added yet.")}<div class="panel-footer"><button class="button" data-delivery-action="add-product" data-id="${esc(delivery.id)}" ${delivery.status !== "DRAFT" ? "disabled" : ""}>+ New product</button></div></section></section><aside class="panel workflow-panel"><div class="eyebrow">WORKFLOW</div><h3>Delivery status</h3><div class="workflow-step active"><strong>Draft</strong><span>Initial stage</span></div><div class="workflow-step ${["WAITING", "READY", "DONE"].includes(delivery.status) ? "active" : ""}"><strong>Waiting</strong><span>Waiting for unavailable stock</span></div><div class="workflow-step ${["READY", "DONE"].includes(delivery.status) ? "active" : ""}"><strong>Ready</strong><span>Ready to deliver</span></div><div class="workflow-step ${delivery.status === "DONE" ? "active" : ""}"><strong>Done</strong><span>Stock delivered</span></div></aside></div>`;
  if (shortages.length) notify(`${shortages.length} delivery line(s) exceed available stock`, "error");
}

function openDeliveryProductForm(deliveryId) {
  formDialog("Add product to delivery", `<label>Stock item<select name="product_id" required><option value="">Select stock item</option>${optionList(state.products)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations)}</select></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`, async (data) => api(`/deliveries/${deliveryId}/items`, { method: "POST", body: JSON.stringify(Object.fromEntries(data)) }), () => renderDeliveryDetail(deliveryId));
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

function renderAccountActions() { const actions = $("#account-actions"); if (!actions) return; actions.innerHTML = state.user ? `<button class="button button-quiet" id="logout-button" title="Log out">Logout</button>` : `<button class="button button-quiet" data-action="auth">Login</button><button class="button button-dark" data-action="auth">Sign up</button>`; }
async function loadUser() { try { state.user = await api("/auth/me"); $("#user-name").textContent = state.user.login_id; $("#user-role").textContent = state.user.role_label || (state.user.role === "ADMIN" ? "Inventory Manager" : "Warehouse Staff"); $("#user-avatar").textContent = state.user.login_id.slice(0, 1).toUpperCase(); $("#connection-status").textContent = "Database connected"; $("#connection-status").className = "connection-dot ok"; renderAccountActions(); } catch { state.user = null; $("#user-name").textContent = "Not signed in"; $("#user-role").textContent = "Connect your account"; $("#user-avatar").textContent = "?"; $("#connection-status").textContent = "Read-only mode"; $("#connection-status").className = "connection-dot"; renderAccountActions(); } }

document.addEventListener("click", async (event) => {
  const kanbanToggle = event.target.closest("[data-toggle-kanban]");
  if (kanbanToggle) {
    const view = kanbanToggle.dataset.toggleKanban;
    if (view === "ledger") { state.operationLayout.ledger = state.operationLayout.ledger === "kanban" ? "list" : "kanban"; renderLedger(); return; }
    renderOperations(view, state.operationLayout[view] === "kanban" ? "list" : "kanban");
    return;
  }
  const viewNode = event.target.closest("[data-view]"); if (viewNode) { render(viewNode.dataset.view); $("#sidebar").classList.remove("open"); return; }
  const receiptRow = event.target.closest("[data-receipt-id]");
  if (receiptRow && !event.target.closest("[data-op-action]")) { renderReceiptDetail(receiptRow.dataset.receiptId); return; }
  const deliveryRow = event.target.closest("[data-delivery-id]");
  if (deliveryRow && !event.target.closest("[data-op-action]")) { renderDeliveryDetail(deliveryRow.dataset.deliveryId); return; }
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
  const deliveryAction = event.target.closest("[data-delivery-action]");
  if (deliveryAction) {
    const action = deliveryAction.dataset.deliveryAction;
    const id = deliveryAction.dataset.id;
    if (action === "print") { window.print(); return; }
    if (action === "add-product") { await loadReferenceData(); openDeliveryProductForm(id); return; }
    try {
      const endpoint = action === "ready" ? `/deliveries/${id}/ready` : action === "validate" ? `/deliveries/${id}/validate` : `/deliveries/${id}/cancel`;
      const options = action === "validate" ? { method: "POST", body: JSON.stringify({ created_by: state.user?.id }) } : { method: "POST" };
      if (action === "validate" && !state.user?.id) throw new Error("Sign in before validating a delivery");
      await api(endpoint, options); notify(action === "ready" ? "Delivery stock status updated" : action === "validate" ? "Delivery completed and stock updated" : "Delivery cancelled"); renderDeliveryDetail(id);
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
  if (action === "quick-stock") return openStockReceiveForm();
  if (action?.startsWith("new-")) return openOperationForm(action.slice(4));
  const stockUpdate = event.target.closest("[data-stock-update]");
  if (stockUpdate) return openStockUpdateForm(stockUpdate);
  if (event.target.closest("[data-close-dialog]")) return event.target.closest("dialog").close();
  if (event.target.closest("#logout-button")) { try { await api("/auth/logout", { method: "POST" }); state.user = null; loadUser(); render("dashboard"); notify("Signed out"); } catch (error) { notify(error.message, "error"); } }
});

$("#mobile-menu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  showAuthMessage("login-message", ""); $("#login-message").classList.remove("show");
  try {
    state.user = await api("/auth/login", { method: "POST", body: JSON.stringify({ login_id: form.get("login_id"), password: form.get("password") }) });
    $("#auth-dialog").close(); loadUser(); render(); notify("Signed in");
  } catch (error) { showAuthMessage("login-message", error.message); }
});
$("#signup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  showAuthMessage("signup-message", ""); $("#signup-message").classList.remove("show");
  try {
    if (form.get("password") !== form.get("confirm_password")) throw new Error("Passwords do not match");
    await api("/auth/signup", { method: "POST", body: JSON.stringify({ login_id: form.get("login_id"), email: form.get("email"), password: form.get("password") }) });
    event.target.reset(); $("#auth-dialog").close(); openDialog(); showAuthMessage("login-message", "Account created successfully. Sign in to continue.", "success"); $("#login-form input[name=login_id]").focus();
  } catch (error) { showAuthMessage("signup-message", error.message); }
});
$("#forgot-password").addEventListener("click", () => { $("#auth-dialog").close(); openResetDialog(); });
$("#request-reset").addEventListener("click", async () => {
  const form = new FormData($("#reset-form"));
  try {
    const result = await api("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email: form.get("email") }) });
    $(".reset-code-fields").classList.add("active"); $("#request-reset").hidden = true; $("#complete-reset").hidden = false;
    $("#reset-message").textContent = result.message;
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
