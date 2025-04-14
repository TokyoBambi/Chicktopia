document.addEventListener("DOMContentLoaded", () => {
  const cartIcon = document.querySelector("#cart-icon");
  const cartPanel = document.querySelector("#shoppingcart");
  const cartItemsContainer = document.getElementById("cart-items");
  const cartTotal = document.getElementById("cart-total");
  const cartCountDisplay = document.querySelector(".cart-badge"); // Element to display cart count
  const cart = [];
  let totalPrice = 0;

  // Initialize cartCount with the value from Django
  let cartCount = cartCountDisplay
    ? parseInt(cartCountDisplay.textContent) || 0
    : 0;

  // Function to toggle the cart visibility
  function toggleCart() {
    if (cartPanel.classList.contains("active")) {
      cartPanel.classList.remove("active"); // Hide the cart panel
    } else {
      cartPanel.classList.add("active"); // Show the cart panel
    }
  }

  // Event listener for the cart icon to toggle the cart
  cartIcon.addEventListener("click", toggleCart);

  // Function to close the cart
  window.closeCart = function () {
    cartPanel.classList.remove("active"); // Hide the cart panel
  };

  // Function to add item to the cart
  function addToCart(title, price, imageUrl) {
    const existingItem = cart.find((item) => item.title === title);

    if (existingItem) {
      cartCount += 1; // Increment cart count
      existingItem.quantity += 1; // Increment quantity if item already exists
    } else {
      cart.push({ title, price, imageUrl, quantity: 1 }); // Add new item
      cartCount += 1; // Increment cart count for the new item
    }
    totalPrice += validatePrice(price);
    updateCartDisplay();
    updateCartCount(); // Update the display of cart count
    cartPanel.classList.add("active"); // Show the cart when an item is added

    // Update Django session (AJAX call)
    updateCartSession(cartCount);
  }

  // Helper function to get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Function to validate price
  function validatePrice(price) {
    const parsedPrice = parseInt(price, 10);
    return isNaN(parsedPrice) ? 0 : parsedPrice; // Return 0 if invalid
  }

  function updateCartSession(count) {
    // Store both the count and the full cart details
    fetch("/retail/update_cart/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        count: count,
        cart_items: cart,
        total_price: totalPrice,
      }),
    }).catch((error) => console.error("Error updating cart:", error));
  }

  // Function to update cart display
  function updateCartDisplay() {
    cartItemsContainer.innerHTML = ""; // Clear previous items

    cart.forEach((item) => {
      const div = document.createElement("div");
      div.className = "cart-item";

      // Create and append the image
      const img = document.createElement("img");

      img.src = item.imageUrl;
      img.alt = item.title;
      img.style.width = "100px";
      img.style.height = "auto";
      img.style.marginRight = "10px";
      div.appendChild(img);

      // Create item details div
      const itemdiv = document.createElement("div");
      itemdiv.className = "item-details";
      div.appendChild(itemdiv);

      // Create and append the title and price
      const title = document.createElement("h4");
      title.textContent = item.title;
      const price = document.createElement("span");
      price.textContent = `Ksh ${item.price}`;
      itemdiv.appendChild(title);
      itemdiv.appendChild(price);

      // Create quantity control container
      const quantityControl = document.createElement("div");
      quantityControl.className = "quantity-control";

      // Create and append the decrement button
      const decrementBtn = document.createElement("button");
      decrementBtn.className = "decrement-btn";
      decrementBtn.textContent = "-";
      quantityControl.appendChild(decrementBtn);

      // Create and append the quantity display
      const quantityDisplay = document.createElement("span");
      quantityDisplay.className = "quantity";
      quantityDisplay.textContent = item.quantity;
      quantityControl.appendChild(quantityDisplay);

      // Create and append the increment button
      const incrementBtn = document.createElement("button");
      incrementBtn.className = "increment-btn";
      incrementBtn.textContent = "+";
      quantityControl.appendChild(incrementBtn);

      // Append quantity control to the cart item
      itemdiv.appendChild(quantityControl);

      // Create the remove button
      const removeBtn = document.createElement("button");
      removeBtn.className = "remove-btn";

      // Create the SVG icon
      const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
    class="bi bi-trash" viewBox="0 0 16 16">
    <path d="M5.5 0a.5.5 0 0 1 .5.5V1h5V.5a.5.5 0 0 1 1 0V1h1a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1H1a1
    1 0 0 1-1-1V1a1 1 0 0 1 1-1h1V.5a.5.5 0 0 1 .5-.5zM4 1v1h8V1H4zm-1 2v11a2 2 0 0 0 2 2h6a2 2 0 0 0 2-
    2V3H3z"/>
    </svg>
    `;

      // Set the inner HTML of the button to the SVG
      removeBtn.innerHTML = svgIcon;
      removeBtn.setAttribute("title", "Remove item");

      // Append the button to the cart item div
      div.appendChild(removeBtn);

      // Append the cart item to the cart items container
      cartItemsContainer.appendChild(div);
    });

    // Update total display
    cartTotal.innerHTML = `<strong>Total: Ksh ${totalPrice}</strong>`;

    // Add event listeners for quantity and remove buttons
    addEventListenersToCartItems();
  }

  // Function to add event listeners to cart item buttons
  function addEventListenersToCartItems() {
    const decrementButtons = document.querySelectorAll(".decrement-btn");
    const incrementButtons = document.querySelectorAll(".increment-btn");
    const removeButtons = document.querySelectorAll(".remove-btn");

    decrementButtons.forEach((button, index) => {
      button.addEventListener("click", () => {
        if (cart[index].quantity > 1) {
          cart[index].quantity -= 1; // Decrease quantity
          totalPrice -= validatePrice(cart[index].price); // Adjust total price

          cartCount -= 1; // Decrement cart count
        } else {
          totalPrice -= validatePrice(cart[index].price); // Adjust total price for removal
          cartCount -= cart[index].quantity; // Decrement cart count by quantity
          cart.splice(index, 1); // Remove item if quantity is 0
        }
        updateCartDisplay();
        updateCartCount(); // Update cart count display
      });
    });

    incrementButtons.forEach((button, index) => {
      button.addEventListener("click", () => {
        cart[index].quantity += 1; // Increase quantity
        totalPrice += validatePrice(cart[index].price); // Adjust total price
        cartCount += 1; // Increment cart count
        updateCartDisplay();
        updateCartCount(); // Update cart count display
      });
    });

    removeButtons.forEach((button, index) => {
      button.addEventListener("click", () => {
        totalPrice -= validatePrice(cart[index].price) * cart[index].quantity; // Subtract total price
        cartCount -= cart[index].quantity; // Decrement cart count by quantity
        cart.splice(index, 1); // Remove item
        updateCartDisplay();
        updateCartCount(); // Update cart count display

        updateCartSession(cartCount); // Update server-side cart count
      });
    });
  }

  // Function to update the cart count display
  function updateCartCount() {
    if (cartCountDisplay) {
      cartCountDisplay.textContent = cartCount; // Update the count display

      // Make sure the count is visible when greater than 0
      cartCountDisplay.style.visibility = cartCount > 0 ? "visible" : "hidden";
    }
  }

  // Initialize cart count display
  updateCartCount();

  // Add event listeners to each Buy Now button
  const buyNowButtons = document.querySelectorAll(".btn");
  buyNowButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault(); // Prevent default anchor behavior

      // Get the parent product-item element

      const productItem = button.closest(".product-item");

      // Retrieve the image URL
      const img = productItem.querySelector("img");
      const imageUrl = img.src; // This is the image URL
      const title = button.getAttribute("data-title");
      const price = button.getAttribute("data-price");

      addToCart(title, price, imageUrl); // Add item to cart with image
    });
  });

  // Function to save cart to session and return a promise
  function saveCartToSession() {
    return new Promise((resolve, reject) => {
      // Create a serializable version of the cart

      const serializableCart = cart.map((item) => ({
        title: item.title,
        price: item.price,
        quantity: item.quantity,
        imageUrl: item.imageUrl,
      }));

      fetch("/retail/update_cart/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
          count: cartCount,
          cart_items: serializableCart,
          total_price: totalPrice,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })

        .then((data) => {
          if (data.success) {
            resolve();
          } else {
            reject(data.error);
          }
        })
        .catch((error) => {
          reject(error);
        });
    });
  }

  // Listen for clicks on the Place Order button
  const placeOrderButton = document.getElementById("place-order-btn");
  if (placeOrderButton) {
    placeOrderButton.addEventListener("click", function (event) {
      event.preventDefault();

      saveCartToSession()
        .then(() => {
          // Use a short timeout to ensure browser has time to process the session
          setTimeout(() => {
            window.location.href = "/retail/checkout/";
          }, 100);
        })
        .catch((error) => {
          alert("There was a problem processing your cart. Please try again.");
        });
    });
  }
});
