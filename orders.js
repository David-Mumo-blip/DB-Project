/* =====================================================
   orders.js  -  the "brain" of orders.html
   ===================================================== */

var VENDOR = getVendorFromURL();
document.getElementById("vendorName").innerText = VENDOR;


/* ---------- ROUTING LOGIC ---------- */

function goBackToVendor() {
  window.location.href = vendorPageName(VENDOR);
}


/* ---------- Showing the orders table ---------- */

function addOrderRow(table, order) {
  var row = table.insertRow();

  row.insertCell(0).innerText = "#" + order.orderNo;
  row.insertCell(1).innerText = order.date;
  row.insertCell(2).innerText = order.studentID;
  row.insertCell(3).innerText = order.foodID;
  row.insertCell(4).innerText = order.foodName;
  row.insertCell(5).innerText = order.quantity;
  row.insertCell(6).innerText = "KSh " + order.total;

  var statusCell = row.insertCell(7);
  var statusTag = document.createElement("span");
  statusTag.innerText = order.status;

  if (order.status === "Ready") {
    statusTag.className = "status-ready";
  } else {
    statusTag.className = "status-pending";
  }
  statusCell.appendChild(statusTag);

  var actionCell = row.insertCell(8);

  if (order.status === "Pending") {
    var readyButton = document.createElement("button");
    readyButton.innerText = "Ready Order";
    readyButton.onclick = function () {
      readyOrder(order.orderNo);
    };
    actionCell.appendChild(readyButton);
  } else {
    actionCell.innerText = "Done";
  }
}

function showOrders() {
  var table = document.getElementById("orderTable");

  while (table.rows.length > 1) {
    table.deleteRow(1);
  }

  var orders = getVendorOrders(VENDOR);

  if (orders.length === 0) {
    var emptyRow = table.insertRow();
    var emptyCell = emptyRow.insertCell(0);
    emptyCell.colSpan = 9;
    emptyCell.className = "empty-note";
    emptyCell.innerText = "No orders yet.";
    return;
  }

  for (var i = 0; i < orders.length; i++) {
    addOrderRow(table, orders[i]);
  }
}


/* ---------- Adding an order (a student ordering) ---------- */

function nextOrderNo(orders) {
  var highest = 0;
  for (var i = 0; i < orders.length; i++) {
    if (orders[i].orderNo > highest) {
      highest = orders[i].orderNo;
    }
  }
  return highest + 1;
}

function addOrder() {
  var studentID = document.getElementById("orderStudentID").value.trim();
  var foodID = document.getElementById("orderFoodID").value.trim();
  var quantity = Number(document.getElementById("orderQuantity").value);

  if (studentID === "") {
    alert("Please enter a Student ID.");
    return;
  }

  var foodFound = findFood(VENDOR, foodID);

  if (foodFound === null) {
    alert("Food ID not found.");
    return;
  }

  if (quantity <= 0 || quantity !== Math.floor(quantity)) {
    alert("Quantity must be a whole number greater than 0.");
    return;
  }

  if (quantity > foodFound.stock) {
    alert("Not enough stock.");
    return;
  }

  var orders = getOrders();

  var order = {
    orderNo: nextOrderNo(orders),
    date: todayText(),
    studentID: studentID,
    vendor: VENDOR,
    foodID: foodID,
    foodName: foodFound.name,
    quantity: quantity,
    total: foodFound.price * quantity,
    status: "Pending"
  };

  orders.push(order);
  saveOrders(orders);

  document.getElementById("orderStudentID").value = "";
  document.getElementById("orderFoodID").value = "";
  document.getElementById("orderQuantity").value = "";

  showOrders();
}


/* ---------- READY ORDER: auto-decrement + notification ---------- */

function readyOrder(orderNo) {
  var orders = getOrders();
  var foods = getFoods();

  // Find the order
  var order = null;
  for (var i = 0; i < orders.length; i++) {
    if (orders[i].orderNo === orderNo) {
      order = orders[i];
    }
  }

  if (order === null || order.status === "Ready") {
    return;
  }

  // Find the product that was ordered
  var food = null;
  for (var j = 0; j < foods.length; j++) {
    if (foods[j].vendor === order.vendor && foods[j].foodID === order.foodID) {
      food = foods[j];
    }
  }

  if (food === null) {
    alert("This product has been removed, so the order cannot be made ready.");
    return;
  }

  if (order.quantity > food.stock) {
    alert("Not enough stock to make this order. Add more stock first.");
    return;
  }

  // AUTO-INCREMENT LOGIC: stock goes down by what the student ordered
  food.stock = food.stock - order.quantity;

  order.status = "Ready";

  saveFoods(foods);
  saveOrders(orders);

  // NOTIFICATION LOGIC: tell the student who ordered
  addNotification(
    order.studentID,
    "Your order #" + order.orderNo + " (" + order.quantity + " x " + order.foodName +
    ") from " + order.vendor + " is ready for pickup!"
  );

  showOrders();
}


/* ---------- Start-up ---------- */

showOrders();
