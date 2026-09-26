const state = { view: "dashboard", user: null, products: [], categories: [], warehouses: [], locations: [], operations: [] };

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
  state.view = view; setActive(view); const title = view === "ledger" ? "Move history" : pretty(view); setPageMeta(title);
  const page = $("#page"); page.innerHTML = `<div class="empty">Loading ${esc(title.toLowerCase())}...</div>`;
  try {
    await loadReferenceData();
    if (view === "dashboard") return renderDashboard();
    if (view === "products") return renderProducts();
    if (view === "stock") return renderStock();
    if (view === "warehouses") return renderWarehouses();
    if (view === "ledger") return renderLedger();
    if (["receipts", "deliveries", "transfers", "adjustments"].includes(view)) return renderOperations(view);
    if (view === "profile") return renderProfile();
  } catch (error) { page.innerHTML = `<div class="panel"><div class="panel-body">${empty("Could not load this view", error.message)}</div></div>`; notify(error.message, "error"); }
}

async function renderDashboard() {
  const [summary, ledger] = await Promise.all([api("/dashboard/summary"), api("/ledger")]);
  const metrics = [["Products in stock", summary.total_products, ""], ["Low stock items", summary.low_stock_items, "warning"], ["Out of stock", summary.out_of_stock_items, "alert"], ["Pending receipts", summary.pending_receipts, ""], ["Pending deliveries", summary.pending_deliveries, ""]];
  const rows = (ledger.items || []).slice(0, 8).map((item) => `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item.product_id?.slice(0, 8) || "-")}</td><td>${esc(item.quantity)}</td><td>${status(item.move_type)}</td><td>${esc(item.created_by?.slice(0, 8) || "-")}</td></tr>`);
  $("#page").innerHTML = `<div class="dashboard-grid">${metrics.map(([label, value, cls]) => `<article class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${value ?? 0}</div></article>`).join("")}</div>
  <div class="content-grid"><section class="panel"><div class="panel-head"><h2>Recent stock movement</h2><button class="button button-quiet" data-view="ledger">View all →</button></div>${table(["Reference","Product","Quantity","Type","Created by"], rows, "No stock movements yet.")}</section><section class="panel"><div class="panel-head"><h2>Quick actions</h2></div><div class="panel-body quick-list"><button class="quick-link" data-view="products"><span>Add a product</span><b>→</b></button><button class="quick-link" data-action="quick-receipt"><span>Record incoming stock</span><b>→</b></button><button class="quick-link" data-view="transfers"><span>Move stock between locations</span><b>→</b></button><button class="quick-link" data-view="adjustments"><span>Adjust a physical count</span><b>→</b></button></div></section></div>`;
}

function renderProducts() {
  const rows = state.products.map((product) => `<tr><td><strong>${esc(product.sku)}</strong></td><td>${esc(product.name)}</td><td>${esc(state.categories.find((item) => item.id === product.category_id)?.name || "Uncategorised")}</td><td>${esc(product.unit || "piece")}</td><td>${esc(product.reorder_level ?? 0)}</td><td>${product.is_active ? status("Ready") : status("Cancelled")}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="toolbar-left"><input class="search" id="product-search" placeholder="Search by name or SKU" value=""></div><div class="toolbar-right"><button class="button button-dark" data-action="new-product">+ New product</button></div></div><section class="panel"><div class="panel-head"><div><h2 class="section-title">Product catalogue</h2><span class="muted">${state.products.length} products</span></div><button class="button" data-view="stock">View stock by location</button></div>${table(["SKU","Product","Category","Unit","Reorder level","Status"], rows, "No products yet. Add the first product to begin tracking stock.")}</section>`;
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

async function renderLedger() {
  const result = await api("/ledger"); const rows = (result.items || []).map((item) => `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item.product_id?.slice(0, 8) || "-")}</td><td>${esc(item.from_location_id?.slice(0, 8) || "-" )}</td><td>${esc(item.to_location_id?.slice(0, 8) || "-")}</td><td class="${item.move_type === "IN" ? "stock-positive" : "stock-negative"}">${item.move_type === "IN" ? "+" : "-"}${esc(item.quantity)}</td><td>${status(item.move_type)}</td></tr>`);
  $("#page").innerHTML = `<div class="page-toolbar"><div class="callout">Every validated receipt, delivery, transfer, and adjustment is recorded here. Incoming movements are shown in green; outgoing movements in red.</div></div><section class="panel">${table(["Reference","Product","From","To","Quantity","Movement"], rows, "No validated movements yet.")}</section>`;
}

async function renderOperations(view) {
  const labels = { receipts: ["Receipts", "Incoming stock from vendors", "receive_from", "Receive from"], deliveries: ["Deliveries", "Outgoing stock for customer shipments", "delivery_address", "Delivery address"], transfers: ["Internal transfers", "Move stock between warehouse locations", "", ""], adjustments: ["Adjustments", "Reconcile recorded quantities with physical counts", "reason", "Reason"] };
  const [heading, description] = labels[view]; const result = await api(`/${view}`); state.operations = result.items || [];
  const rows = state.operations.map((item) => { const nextAction = item.status === "DRAFT" && view !== "adjustments" ? "ready" : item.status === "READY" || (item.status === "DRAFT" && view === "adjustments") ? "validate" : ""; const actionLabel = nextAction === "ready" ? "Mark ready" : nextAction === "validate" ? "Validate" : "-"; return `<tr><td><strong>${esc(item.reference)}</strong></td><td>${esc(item[labels[view][2]] || "-")}</td><td>${esc(item.schedule_date || "-")}</td><td>${status(item.status)}</td><td>${nextAction ? `<button class="button button-quiet" data-op-action="${nextAction}" data-op-type="${view}" data-id="${esc(item.id)}">${actionLabel} →</button>` : `<span class="muted">Complete</span>`}</td></tr>`; });
  const detailColumn = view === "transfers" ? "Route" : view === "adjustments" ? "Reason" : view === "deliveries" ? "Address" : "Supplier";
  $("#page").innerHTML = `<div class="page-toolbar"><div><div class="section-title">${heading}</div><div class="muted">${description}</div></div><button class="button button-dark" data-action="new-${view}">+ New ${heading.slice(0, -1).toLowerCase()}</button></div><section class="panel">${table(["Reference",detailColumn,"Schedule date","Status",""], rows, `No ${heading.toLowerCase()} yet.`)}</section>`;
}

function renderProfile() {
  const user = state.user; $("#page").innerHTML = `<section class="panel"><div class="panel-head"><div><div class="eyebrow">ACCOUNT</div><h2 class="section-title">My profile</h2></div></div><div class="panel-body">${user ? `<div class="cards"><div class="mini-card"><span class="muted">Login ID</span><strong>${esc(user.login_id)}</strong></div><div class="mini-card"><span class="muted">Email</span><strong>${esc(user.email)}</strong></div><div class="mini-card"><span class="muted">Role</span><strong>${esc(user.role)}</strong></div></div>` : `<div class="callout">You are browsing in read-only mode. Sign in to create operations and manage your profile.</div><br><button class="button button-dark" data-action="auth">Sign in</button>`}</div></section>`;
}

function openDialog(mode = "signin") {
  const dialog = $("#auth-dialog");
  const signup = mode === "signup";
  const email = dialog.querySelector("[name=email]");
  const confirm = dialog.querySelector("[name=confirm_password]");
  const password = dialog.querySelector("[name=password]");
  dialog.classList.toggle("auth-signup", signup);
  $("#auth-title").textContent = signup ? "Create account" : "Sign in";
  $("#auth-switch").textContent = signup ? "I already have an account" : "Create account";
  email.required = signup; confirm.required = signup;
  if (signup) {
    password.minLength = 8;
    password.pattern = "(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}";
    password.title = "Use at least 8 characters with an uppercase letter, number, and special character.";
    password.autocomplete = "new-password";
  } else {
    password.removeAttribute("minlength"); password.removeAttribute("pattern"); password.removeAttribute("title"); password.autocomplete = "current-password";
  }
  dialog.dataset.mode = mode; dialog.showModal();
}

function formDialog(title, content, submit) { const dialog = document.createElement("dialog"); dialog.className = "modal"; dialog.innerHTML = `<div class="modal-head"><div><div class="eyebrow">NEW RECORD</div><h2>${title}</h2></div><button class="icon-button" data-close-dialog>×</button></div><form class="form-grid">${content}<div class="form-actions"><button type="button" class="button button-quiet" data-close-dialog>Cancel</button><button class="button button-dark">Create</button></div></form>`; document.body.append(dialog); dialog.showModal(); dialog.querySelector("form").addEventListener("submit", async (event) => { event.preventDefault(); try { await submit(new FormData(event.target)); dialog.close(); dialog.remove(); notify(`${title} created`); render(); } catch (error) { notify(error.message, "error"); } }); dialog.addEventListener("close", () => dialog.remove()); }

function openProductForm() { formDialog("New product", `<label>SKU / code<input name="sku" required></label><label>Product name<input name="name" required></label><label>Category<select name="category_id"><option value="">Uncategorised</option>${optionList(state.categories)}</select></label><label>Unit of measure<input name="unit" value="piece"></label><label>Unit cost<input name="unit_cost" type="number" min="0" step="0.01" value="0"></label><label>Reorder level<input name="reorder_level" type="number" min="0" step="0.001" value="0"></label><label class="wide">Description<textarea name="description"></textarea></label>`, async (data) => api("/products", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) })); }
function openWarehouseForm() { formDialog("New warehouse", `<label>Warehouse name<input name="name" required></label><label>Short code<input name="short_code" required></label><label class="wide">Address<textarea name="address"></textarea></label>`, async (data) => api("/warehouses", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) })); }
function openOperationForm(type) {
  const isReceipt = type === "receipts";
  const isDelivery = type === "deliveries";
  const userId = state.user?.id || "";
  let fields;
  if (isReceipt || isDelivery) {
    fields = `<label>Reference<input name="reference" placeholder="MAIN/${isReceipt ? "IN" : "OUT"}/0001" required></label><label>Responsible user ID<input name="responsible_id" value="${esc(userId)}" placeholder="UUID" required></label><label>Warehouse<select name="warehouse_id" required><option value="">Select warehouse</option>${optionList(state.warehouses)}</select></label><label>Schedule date<input name="schedule_date" type="date"></label><label>${isReceipt ? "Receive from" : "Delivery address"}<input name="${isReceipt ? "receive_from" : "delivery_address"}"></label><label>Product<select name="product_id" required><option value="">Select product</option>${optionList(state.products)}</select></label><label>Location<select name="location_id" required><option value="">Select location</option>${optionList(state.locations)}</select></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" required></label>`;
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
  const viewNode = event.target.closest("[data-view]"); if (viewNode) { render(viewNode.dataset.view); $("#sidebar").classList.remove("open"); return; }
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
  if (action === "quick-receipt") return openOperationForm("receipts");
  if (action?.startsWith("new-")) return openOperationForm(action.slice(4));
  if (event.target.closest("[data-close-dialog]")) return event.target.closest("dialog").close();
  if (event.target.closest("#logout-button")) { try { await api("/auth/logout", { method: "POST" }); state.user = null; loadUser(); render("dashboard"); notify("Signed out"); } catch (error) { notify(error.message, "error"); } }
});

$("#mobile-menu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
$("#auth-switch").addEventListener("click", () => openDialog($("#auth-dialog").dataset.mode === "signup" ? "signin" : "signup"));
$("#auth-form").addEventListener("submit", async (event) => { event.preventDefault(); const form = new FormData(event.target); const mode = $("#auth-dialog").dataset.mode; try { if (mode === "signup" && form.get("password") !== form.get("confirm_password")) throw new Error("Passwords do not match"); state.user = await api(mode === "signup" ? "/auth/signup" : "/auth/login", { method: "POST", body: JSON.stringify({ login_id: form.get("login_id"), email: form.get("email"), password: form.get("password") }) }); $("#auth-dialog").close(); loadUser(); render(); notify(mode === "signup" ? "Account created" : "Signed in"); } catch (error) { notify(error.message, "error"); } });
$(".user-chip").addEventListener("click", () => openDialog());

loadUser(); render();
