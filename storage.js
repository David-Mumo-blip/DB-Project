/* =====================================================
   storage.js  -  the SHARED NOTEBOOK for every page
   Every page loads this file first, so they can all
   read and write the same information (products,
   orders, notifications) using the browser's
   localStorage.
   ===================================================== */

// The "labels" (keys) of the pages in our notebook
var KEY_FOODS = "hh_foods";
var KEY_ORDERS = "hh_orders";
var KEY_NOTES = "hh_notifications";

// Every vendor page in the project
var VENDORS = ["Pate", "Kilimanjaro", "Georgie", "Kerinton"];


/* ---------- Basic read / write helpers ---------- */

function loadData(key) {
  var text = localStorage.getItem(key);
  if (text === null) {
    return [];
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    return [];
  }
}

function saveData(key, list) {
  localStorage.setItem(key, JSON.stringify(list));
}

function getFoods() { return loadData(KEY_FOODS); }
function saveFoods(foods) { saveData(KEY_FOODS, foods); }

function getOrders() { return loadData(KEY_ORDERS); }
function saveOrders(orders) { saveData(KEY_ORDERS, orders); }

function getNotes() { return loadData(KEY_NOTES); }
function saveNotes(notes) { saveData(KEY_NOTES, notes); }


/* ---------- Vendor-specific helpers ---------- */

// Only the products that belong to ONE vendor
function getVendorFoods(vendor) {
  var all = getFoods();
  var mine = [];
  for (var i = 0; i < all.length; i++) {
    if (all[i].vendor === vendor) {
      mine.push(all[i]);
    }
  }
  return mine;
}

// Only the orders that belong to ONE vendor
function getVendorOrders(vendor) {
  var all = getOrders();
  var mine = [];
  for (var i = 0; i < all.length; i++) {
    if (all[i].vendor === vendor) {
      mine.push(all[i]);
    }
  }
  return mine;
}

// Find one product by vendor + Food ID (returns null if missing)
function findFood(vendor, foodID) {
  var foods = getVendorFoods(vendor);
  for (var i = 0; i < foods.length; i++) {
    if (foods[i].foodID === foodID) {
      return foods[i];
    }
  }
  return null;
}

// Revenue = total of all orders the vendor has marked READY
function getRevenue(vendor) {
  var orders = getVendorOrders(vendor);
  var total = 0;
  for (var i = 0; i < orders.length; i++) {
    if (orders[i].status === "Ready") {
      total = total + orders[i].total;
    }
  }
  return total;
}

function getGoal(vendor) {
  return Number(localStorage.getItem("hh_goal_" + vendor)) || 0;
}

function saveGoal(vendor, amount) {
  localStorage.setItem("hh_goal_" + vendor, amount);
}


/* ---------- Notifications ---------- */

function addNotification(studentID, message) {
  var notes = getNotes();
  notes.push({
    studentID: studentID,
    message: message,
    date: todayText()
  });
  saveNotes(notes);
}


/* ---------- Small utilities ---------- */

function todayText() {
  var today = new Date();
  return today.getDate() + "/" + (today.getMonth() + 1) + "/" + today.getFullYear();
}

// Reads  ?vendor=Pate  from the address bar (used for routing)
function getVendorFromURL() {
  var params = new URLSearchParams(window.location.search);
  var name = params.get("vendor");
  if (VENDORS.indexOf(name) === -1) {
    return "Pate";
  }
  return name;
}

// "Pate" -> "pate.html"
function vendorPageName(vendor) {
  return vendor.toLowerCase() + ".html";
}


/* ---------- Sample products (first visit only) ---------- */

function seedSampleProducts() {
  if (localStorage.getItem(KEY_FOODS) === null) {
    saveFoods([
      { vendor: "Pate", name: "Chapati",icon: "" , foodID: "P001", price: 30, stock: 20 },
      { vendor: "Pate", name: "Beef Samosa", icon: "", foodID: "P002", price: 50, stock: 15 },
      { vendor: "Pate", name: "Mandazi", icon: "", foodID: "P003", price: 20, stock: 30 }
    ]);
  }
}

seedSampleProducts();
