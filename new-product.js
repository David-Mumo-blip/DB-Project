/* =====================================================
   new-product.js  -  the "brain" of new-product.html
   The vendor name comes from the address bar, e.g.
   new-product.html?vendor=Pate
   ===================================================== */

var VENDOR = getVendorFromURL();
document.getElementById("vendorName").innerText = VENDOR;


/* ---------- ROUTING LOGIC ---------- */

function goBackToVendor() {
  window.location.href = vendorPageName(VENDOR);
}

function goToOrders() {
  window.location.href = "orders.html?vendor=" + VENDOR;
}


/* ---------- Showing a message under the form ---------- */

function showMessage(text) {
  document.getElementById("message").innerText = text;
}


/* ---------- Add the product ---------- */

function addFood() {
  var name = document.getElementById("foodName").value.trim();
  var icon = document.getElementById("foodIcon").value.trim();
  var foodID = document.getElementById("foodID").value.trim();
  var priceText = document.getElementById("foodPrice").value;
  var stockText = document.getElementById("foodStock").value;

  var price = Number(priceText);
  var stock = Number(stockText);

 // 1. Check the for
  if (name === "" || foodID === "") {
    showMessage("Please fill in the food name and the Food ID.");
    return;
  }

  if (priceText === "" || price <= 0) {
    showMessage("Please enter a price greater than 0.");
    return;
  }

  if (stockText === "" || stock < 0) {
    showMessage("Please enter a stock amount (0 or more).");
    return;
  }

  if (icon === "") {
    icon = "🍽️";
  }

  // 2. Make sure this vendor does not already use that Food ID
  if (findFood(VENDOR, foodID) !== null) {
    showMessage("That Food ID is already used. Please choose a different one.");
    return;
  }

  // 3. Build the product and save it in the shared notebook
  var food = {
    vendor: VENDOR,
    name: name,
    icon: icon,
    foodID: foodID,
    price: price,
    stock: stock
  };

  var foods = getFoods();
  foods.push(food);
  saveFoods(foods);

  // 4. REFLECTION: go back to the vendor page where it now appears
  goBackToVendor();
}
