/* =====================================================
   Georgie.js  -  the "brain" of pate.html
   To make Kilimanjaro / Georgie / Kerinton pages, copy
   this file and change the VENDOR name on the next line.
   ===================================================== */

var VENDOR = "Georgie";


/* ---------- ROUTING LOGIC ---------- */

function goToOrders() {
  window.location.href = "orders.html?vendor=" + VENDOR;
}

function goToNewProduct() {
  window.location.href = "new-product.html?vendor=" + VENDOR;
}


/* ---------- Building the stock table ---------- */

// Makes one button and tells it what to do when clicked
function buildButton(label, extraClass, whenClicked) {
  var button = document.createElement("button");
  button.innerText = label;
  if (extraClass !== "") {
    button.className = extraClass;
  }
  button.onclick = whenClicked;
  return button;
}

// Adds ONE row (one product) to the table
function addFoodRow(table, food) {
  var row = table.insertRow();

  row.insertCell(0).innerText = food.name;
  row.insertCell(1).innerText = food.icon;
  row.insertCell(2).innerText = food.foodID;
  row.insertCell(3).innerText = "KSh " + food.price;
  row.insertCell(4).innerText = food.stock;

  var addButton = buildButton("+", "", function () {
    addStock(food.foodID);
  });

  var removeButton = buildButton("-", "", function () {
    removeStock(food.foodID);
  });

  var deleteButton = buildButton("Remove", "danger-btn", function () {
    deleteProduct(food.foodID);
  });

  row.insertCell(5).appendChild(addButton);
  row.insertCell(6).appendChild(removeButton);
  row.insertCell(7).appendChild(deleteButton);
}

function showStock() {
  var table = document.getElementById("stockTable");

  // Clear every row except the heading row
  while (table.rows.length > 1) {
    table.deleteRow(1);
  }

  var foods = getVendorFoods(VENDOR);

  if (foods.length === 0) {
    var emptyRow = table.insertRow();
    var emptyCell = emptyRow.insertCell(0);
    emptyCell.colSpan = 8;
    emptyCell.className = "empty-note";
    emptyCell.innerText = "No products yet. Click + Add Product to create one.";
    return;
  }

  for (var i = 0; i < foods.length; i++) {
    addFoodRow(table, foods[i]);
  }
}


/* ---------- Stock buttons (+ and -) ---------- */

function changeStock(foodID, change) {
  var foods = getFoods();

  for (var i = 0; i < foods.length; i++) {
    if (foods[i].vendor === VENDOR && foods[i].foodID === foodID) {
      var newStock = foods[i].stock + change;
      if (newStock < 0) {
        newStock = 0;
      }
      foods[i].stock = newStock;
    }
  }

  saveFoods(foods);
  showStock();
}

function addStock(foodID) {
  changeStock(foodID, 1);
}

function removeStock(foodID) {
  changeStock(foodID, -1);
}


/* ---------- Remove button: deletes the whole product ---------- */

function deleteProduct(foodID) {
  var sure = confirm("Remove this product completely? This cannot be undone.");
  if (sure === false) {
    return;
  }

  var foods = getFoods();
  var keep = [];

  for (var i = 0; i < foods.length; i++) {
    var isThisOne = (foods[i].vendor === VENDOR && foods[i].foodID === foodID);
    if (isThisOne === false) {
      keep.push(foods[i]);
    }
  }

  saveFoods(keep);
  showStock();
}


/* ---------- Revenue and goal ---------- */

function setGoal() {
  var goal = Number(document.getElementById("goalInput").value);
  saveGoal(VENDOR, goal);
  showRevenue();
}

function showRevenue() {
  var revenue = getRevenue(VENDOR);
  var goal = getGoal(VENDOR);

  document.getElementById("revenue").innerText = revenue;
  document.getElementById("goal").innerText = goal;

  var percent = 0;

  if (goal > 0) {
    percent = (revenue / goal) * 100;
  }

  if (percent > 100) {
    percent = 100;
  }

  document.getElementById("percent").innerText = Math.round(percent);
  document.getElementById("progressBar").style.width = percent + "%";
}


/* ---------- Orders button badge: "Orders (2)" ---------- */

function updateOrdersButton() {
  var orders = getVendorOrders(VENDOR);
  var pending = 0;

  for (var i = 0; i < orders.length; i++) {
    if (orders[i].status === "Pending") {
      pending = pending + 1;
    }
  }

  var button = document.getElementById("ordersButton");

  if (pending > 0) {
    button.innerText = "Orders (" + pending + ")";
  } else {
    button.innerText = "Orders";
  }
}


/* ---------- Start-up ---------- */

function refreshPage() {
  showStock();
  showRevenue();
  updateOrdersButton();
}

refreshPage();

// Runs again when the vendor comes back with the browser's Back button
window.addEventListener("pageshow", refreshPage);
