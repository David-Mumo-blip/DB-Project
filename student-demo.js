/* =====================================================
   student-demo.js - a tiny stand-in for the student side.
   Your teammates' real student pages will read and write
   the same shared notebook (storage.js).
   ===================================================== */

var VENDOR = getVendorFromURL();
document.getElementById("vendorName").innerText = VENDOR;


/* ---------- Menu (REFLECTION: same products the vendor sees) ---------- */

function addMenuRow(table, food) {
  var row = table.insertRow();

  row.insertCell(0).innerText = food.name;
  row.insertCell(1).innerText = food.icon;
  row.insertCell(2).innerText = "KSh " + food.price;
  row.insertCell(3).innerText = food.stock;

  var quantityBox = document.createElement("input");
  quantityBox.type = "number";
  quantityBox.min = "1";
  quantityBox.value = "1";
  row.insertCell(4).appendChild(quantityBox);

  var orderButton = document.createElement("button");
  orderButton.innerText = "Order";

  if (food.stock === 0) {
    orderButton.innerText = "Sold out";
    orderButton.disabled = true;
  }

  orderButton.onclick = function () {
    placeOrder(food, Number(quantityBox.value));
  };

  row.insertCell(5).appendChild(orderButton);
}

function showMenu() {
  var table = document.getElementById("menuTable");

  while (table.rows.length > 1) {
    table.deleteRow(1);
  }

  var foods = getVendorFoods(VENDOR);

  if (foods.length === 0) {
    var emptyRow = table.insertRow();
    var emptyCell = emptyRow.insertCell(0);
    emptyCell.colSpan = 6;
    emptyCell.className = "empty-note";
    emptyCell.innerText = "No products available right now.";
    return;
  }

  for (var i = 0; i < foods.length; i++) {
    addMenuRow(table, foods[i]);
  }
}


/* ---------- Placing an order ---------- */

function placeOrder(food, quantity) {
  var studentID = document.getElementById("studentID").value.trim();

  if (studentID === "") {
    alert("Please type your Student ID first.");
    return;
  }

  if (quantity <= 0 || quantity !== Math.floor(quantity)) {
    alert("Quantity must be a whole number greater than 0.");
    return;
  }

  if (quantity > food.stock) {
    alert("Not enough stock.");
    return;
  }

  var orders = getOrders();
  var highest = 0;
  for (var i = 0; i < orders.length; i++) {
    if (orders[i].orderNo > highest) {
      highest = orders[i].orderNo;
    }
  }

  orders.push({
    orderNo: highest + 1,
    date: todayText(),
    studentID: studentID,
    vendor: VENDOR,
    foodID: food.foodID,
    foodName: food.name,
    quantity: quantity,
    total: food.price * quantity,
    status: "Pending"
  });

  saveOrders(orders);
  alert("Order placed! You will be notified when it is ready.");
}


/* ---------- NOTIFICATION LOGIC: what the student sees ---------- */

function showNotifications() {
  var box = document.getElementById("notificationList");
  var studentID = document.getElementById("studentID").value.trim();
  box.innerHTML = "";

  if (studentID === "") {
    box.innerText = "Type your Student ID above to see your notifications.";
    return;
  }

  var notes = getNotes();
  var found = 0;

  // Newest first
  for (var i = notes.length - 1; i >= 0; i--) {
    if (notes[i].studentID === studentID) {
      var card = document.createElement("div");
      card.className = "note-card";
      card.innerText = notes[i].message;

      var dateLine = document.createElement("div");
      dateLine.className = "note-date";
      dateLine.innerText = notes[i].date;
      card.appendChild(dateLine);

      box.appendChild(card);
      found = found + 1;
    }
  }

  if (found === 0) {
    box.innerText = "No notifications yet.";
  }
}


/* ---------- Start-up ---------- */

showMenu();
showNotifications();

// "storage" fires when ANOTHER tab changes the shared notebook,
// so this page updates itself when the vendor clicks Ready Order.
window.addEventListener("storage", function () {
  showMenu();
  showNotifications();
});
