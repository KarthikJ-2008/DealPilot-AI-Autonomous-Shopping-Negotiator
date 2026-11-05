/**
 * DealPilot AI — Autonomous Shopping Negotiator
 * Frontend Logic, State Management, AG Grid & API Integration
 */

/* =====================================================================
   1. GLOBAL STATE & CONFIGURATION
   ===================================================================== */
const API_BASE_URL = "http://localhost:8000/api";
let isBackendConnected = false;

// Application state
const AppState = {
  currentView: 'dashboard',
  userPolicies: {
    maxBudget: 300,
    approvalThreshold: 150,
    maxRounds: 3,
    approvedMerchants: ["Amazon Retail", "ElectroDirect", "SoundHut", "BestBuy", "B&H Photo"]
  },
  currentProduct: {
    id: "prod-sony-wh1000",
    name: "Sony WH-1000XM4 Wireless Noise-Canceling Headphones",
    brand: "Sony",
    merchant: "ElectroDirect",
    originalPrice: 278.00,
    targetPrice: 230.00,
    currentNegotiatedPrice: 235.00,
    currency: "USD",
    rating: 4.8,
    deliveryInfo: "2-Day Express (Free via DealPilot)",
    savings: 43.00,
    status: "Accepted"
  },
  negotiationSession: {
    id: "NEG-8092",
    round: 2,
    maxRounds: 3,
    status: "ACTIVE",
    history: [
      { sender: "ai", text: "Product 'Sony WH-1000XM4' indexed across 5 retail stores. Best initial candidate: ElectroDirect ($278.00).", time: "10:14 AM" },
      { sender: "ai", text: "Target established: $230.00 based on your $280 ceiling and competitor SoundHut ($259.00).", time: "10:15 AM" },
      { sender: "ai", text: "Offer dispatched to ElectroDirect merchant portal: $225.00 cash settlement.", time: "10:15 AM" },
      { sender: "merchant", text: "Merchant Response: We cannot meet $225.00, but we can offer $245.00 with complimentary express handling.", time: "10:16 AM" },
      { sender: "ai", text: "Counteroffer synthesized: Demanding final price of $235.00 with warranty preserved.", time: "10:16 AM" },
      { sender: "merchant", text: "Merchant Response: Offer accepted! $235.00 locked for 60 minutes.", time: "10:17 AM" }
    ]
  },
  notifications: [
    { id: 1, title: "Offer Accepted by ElectroDirect", desc: "Sony WH-1000XM4 accepted at $235.00. Ready for checkout.", unread: true, time: "2 min ago", type: "success" },
    { id: 2, title: "Approval Required", desc: "Purchase amount ($235.00) exceeds auto-checkout limit ($150.00).", unread: true, time: "3 min ago", type: "warning" },
    { id: 3, title: "Price Drop Monitored", desc: "Bose 700 dropped by $15 at SoundHut.", unread: true, time: "1 hour ago", type: "info" }
  ],
  comparisonProducts: [
    { id: 1, product: "Sony WH-1000XM4", brand: "Sony", merchant: "ElectroDirect", originalPrice: 278, rating: 4.8, delivery: "2-Day Express", status: "Negotiated ($235)", finalPrice: 235, savings: 43, approved: true },
    { id: 2, product: "Sony WH-1000XM4", brand: "Sony", merchant: "SoundHut", originalPrice: 259, rating: 4.6, delivery: "Standard 4-Day", status: "Initial Listed", finalPrice: 259, savings: 0, approved: true },
    { id: 3, product: "Sony WH-1000XM4", brand: "Sony", merchant: "BestBuy Retail", originalPrice: 299, rating: 4.9, delivery: "Next-Day Air", status: "Negotiation Stalled", finalPrice: 279, savings: 20, approved: true },
    { id: 4, product: "Sony WH-1000XM4", brand: "Sony", merchant: "MarketplaceSeller-9", originalPrice: 220, rating: 3.2, delivery: "10-14 Days", status: "Blocked (Unverified)", finalPrice: 220, savings: 58, approved: false },
    { id: 5, product: "Sony WH-1000XM4", brand: "Sony", merchant: "B&H Photo Video", originalPrice: 279, rating: 4.8, delivery: "2-Day Ground", status: "Eligible for Bot", finalPrice: 279, savings: 0, approved: true }
  ],
  transactionsLedger: [
    { id: "TXN-8932014", product: "Sony WH-1000XM4", merchant: "ElectroDirect", origPrice: 278.00, finalPrice: 235.00, savings: 43.00, status: "COMPLETED", date: "2026-03-31" },
    { id: "TXN-7741290", product: "Apple AirPods Pro 2", merchant: "BestBuy", origPrice: 249.00, finalPrice: 219.00, savings: 30.00, status: "COMPLETED", date: "2026-03-22" },
    { id: "TXN-6619042", product: "Logitech MX Master 3S", merchant: "Amazon Retail", origPrice: 99.00, finalPrice: 82.00, savings: 17.00, status: "COMPLETED", date: "2026-03-10" },
    { id: "TXN-5520981", product: "Dell UltraSharp 27 4K", merchant: "B&H Photo", origPrice: 580.00, finalPrice: 495.00, savings: 85.00, status: "COMPLETED", date: "2026-02-28" }
  ]
};

/* =====================================================================
   2. REUSABLE API HELPER WITH TRANSPARENT MOCK FALLBACK
   ===================================================================== */
const ApiService = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500); // quick timeout for fallback
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        }
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      setBackendOnlineState(true);
      return await response.json();
    } catch (err) {
      // Fall back seamlessly to local mock controller
      console.warn(`[DealPilot Client] Endpoint ${endpoint} fallback: ${err.message}`);
      setBackendOnlineState(false);
      return ApiService.mockController(endpoint, options);
    }
  },

  mockController(endpoint, options) {
    console.info(`[DealPilot Mock Engine] Handled request for: ${endpoint}`);
    const method = options.method || 'GET';
    
    if (endpoint === '/health') {
      return { status: "mock_offline_fallback", timestamp: new Date().toISOString() };
    }
    if (endpoint === '/policies') {
      return AppState.userPolicies;
    }
    if (endpoint === '/purchases/approve') {
      return { approved: true, orderId: "ORD-" + Math.floor(Math.random() * 899999 + 100000) };
    }
    if (endpoint === '/payments/create-order') {
      return { id: "PAYPAL-ORDER-" + Math.floor(Math.random() * 900000 + 100000), status: "CREATED" };
    }
    if (endpoint === '/payments/capture-order') {
      return { captureId: "CAP-" + Math.floor(Math.random() * 900000 + 100000), status: "COMPLETED" };
    }
    if (endpoint.includes('/counteroffer')) {
      return {
        round: 3,
        responsePrice: 235.00,
        accepted: true,
        message: "Merchant conceded to counteroffer."
      };
    }
    return { success: true };
  }
};

function setBackendOnlineState(online) {
  isBackendConnected = online;
  const dot = document.getElementById('apiStatusDot');
  const label = document.getElementById('apiStatusLabel');
  if (dot && label) {
    if (online) {
      dot.classList.add('online');
      label.textContent = "FastAPI Connected";
    } else {
      dot.classList.remove('online');
      label.textContent = "Offline Demo Mode";
    }
  }
}

/* =====================================================================
   3. NAVIGATION & ROUTING ENGINE
   ===================================================================== */
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item[data-view]');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const viewId = item.getAttribute('data-view');
      switchView(viewId);
    });
  });

  // Mobile Menu button
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('appSidebar');
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
}

function switchView(viewId) {
  AppState.currentView = viewId;

  // Update active nav link
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('active');
    if (el.getAttribute('data-view') === viewId) {
      el.classList.add('active');
    }
  });

  // Hide all screens & show selected
  document.querySelectorAll('.view-screen').forEach(screen => {
    screen.classList.remove('active');
  });

  const targetScreen = document.getElementById(`view-${viewId}`);
  if (targetScreen) {
    targetScreen.classList.add('active');
  }

  // Close mobile drawer if opened
  const sidebar = document.getElementById('appSidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
  }

  // Trigger redraws if grid/chart is initialized
  if (viewId === 'comparison' && gridApi) {
    setTimeout(() => gridApi.sizeColumnsToFit(), 60);
  }
  if (viewId === 'analytics') {
    if (analyticsGridApi) setTimeout(() => analyticsGridApi.sizeColumnsToFit(), 60);
    renderAnalyticsCharts();
  }
}

/* =====================================================================
   4. SCREEN 1: DASHBOARD LOGIC
   ===================================================================== */
function handleHeroSubmit(e) {
  e.preventDefault();
  const query = document.getElementById('heroQueryInput').value.trim();
  const budget = parseFloat(document.getElementById('heroBudgetInput').value);

  if (!query || isNaN(budget) || budget <= 0) {
    showToast("Please provide a valid product query and budget.", "warning");
    return;
  }

  // Populate Screen 2
  const searchNameInput = document.getElementById('searchProductName');
  const searchBudgetInput = document.getElementById('searchMaxBudget');
  if (searchNameInput) searchNameInput.value = query;
  if (searchBudgetInput) searchBudgetInput.value = budget;
  
  showToast(`Initiating discovery for "${query}" under $${budget}...`, "info");
  switchView('search');
  executeProductSearch();
}

function renderDashboardRecentList() {
  const container = document.getElementById('dashboardRecentSessionsList');
  if (!container) return;

  const sessions = [
    { title: "Sony WH-1000XM4", store: "ElectroDirect", saved: "$43.00", status: "Deal Ready" },
    { title: "Bose QuietComfort 45", store: "SoundHut", saved: "$25.00", status: "Counteroffer Sent" },
    { title: "AirPods Max Space Gray", store: "BestBuy", saved: "$50.00", status: "Budget Exceeded" }
  ];

  container.innerHTML = sessions.map(s => `
    <div style="display:flex; justify-content:space-between; align-items:center; padding:14px; background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:var(--radius-sm); margin-bottom:10px;">
      <div>
        <div style="font-weight:600; font-size:0.88rem; color:#fff;">${s.title}</div>
        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${s.store} &bull; Potential Savings: <span style="color:#34D399; font-weight:600;">${s.saved}</span></div>
      </div>
      <span class="badge ${s.status === 'Deal Ready' ? 'badge-success' : (s.status.includes('Budget') ? 'badge-danger' : 'badge-warning')}">${s.status}</span>
    </div>
  `).join('');
}

/* =====================================================================
   5. SCREEN 2: PRODUCT SEARCH & GRID
   ===================================================================== */
let currentProductsList = [
  {
    id: "prod-1",
    name: "Sony WH-1000XM4 Wireless Noise-Canceling",
    brand: "Sony",
    merchant: "ElectroDirect",
    price: 278.00,
    rating: 4.8,
    avail: "In Stock",
    url: "https://electrodirect.com/item/wh-1000xm4",
    img: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
  },
  {
    id: "prod-2",
    name: "Sony WH-1000XM4 Headphones (Black)",
    brand: "Sony",
    merchant: "SoundHut",
    price: 259.00,
    rating: 4.6,
    avail: "In Stock (3 left)",
    url: "https://soundhut.store/products/sony-xm4",
    img: "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&q=80"
  },
  {
    id: "prod-3",
    name: "Sony WH-1000XM4 Bluetooth ANC",
    brand: "Sony",
    merchant: "BestBuy",
    price: 299.99,
    rating: 4.9,
    avail: "Pickup Ready",
    url: "https://bestbuy.com/site/sony-headphones",
    img: "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&q=80"
  },
  {
    id: "prod-4",
    name: "Bose QuietComfort 45 Over-Ear",
    brand: "Bose",
    merchant: "ElectroDirect",
    price: 279.00,
    rating: 4.7,
    avail: "In Stock",
    url: "https://electrodirect.com/item/qc45",
    img: "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=500&q=80"
  }
];

async function executeProductSearch(e) {
  if (e) e.preventDefault();
  const pName = document.getElementById('searchProductName')?.value || "Headphones";
  const pBrand = document.getElementById('searchBrand')?.value || "";
  const pBudget = parseFloat(document.getElementById('searchMaxBudget')?.value || 280);

  showToast(`Querying retail merchant APIs for "${pName}"...`, "info");

  // Attempt backend API call
  try {
    const res = await ApiService.request('/products/search', {
      method: 'POST',
      body: JSON.stringify({
        product_name: pName,
        brand: pBrand,
        budget: pBudget,
        requirements: []
      })
    });

    if (res && res.products && res.products.length > 0) {
      currentProductsList = res.products.map((p, idx) => {
        // If image is missing or is the default headphone image and user searched for something else, resolve dynamically
        const isDefaultHeadphone = !p.image || p.image.includes("1505740420928") || p.image.includes("1583394838336") || p.image.includes("1546435770") || p.image.includes("1484704849700");
        const resolvedImg = (isDefaultHeadphone && !pName.toLowerCase().includes("headphone") && !pName.toLowerCase().includes("xm4") && !pName.toLowerCase().includes("wh-1000")) 
          ? resolveProductImage(p.name || pName, p.brand || pBrand, idx)
          : (p.image || resolveProductImage(p.name || pName, p.brand || pBrand, idx));
        return {
          id: p.id,
          name: p.name,
          brand: p.brand || pBrand || "Featured",
          merchant: p.merchant,
          price: p.price,
          rating: p.rating || 4.7,
          avail: p.availability || "In Stock",
          url: p.url || "#",
          img: resolvedImg
        };
      });
    }
  } catch (err) {
    // Dynamic generation if mock
    generateDynamicSearchResults(pName, pBrand, pBudget);
  }

  renderProductGrid();
}

// Intelligent Image Resolver based on product keyword detection
function resolveProductImage(queryName, brandName, index = 0) {
  const q = `${queryName} ${brandName}`.toLowerCase();
  
  const catalog = {
    phone: [
      "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&q=80",
      "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&q=80",
      "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600&q=80",
      "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=600&q=80"
    ],
    laptop: [
      "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&q=80",
      "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80",
      "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=600&q=80",
      "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&q=80"
    ],
    watch: [
      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
      "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600&q=80",
      "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&q=80",
      "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&q=80"
    ],
    camera: [
      "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&q=80",
      "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&q=80",
      "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&q=80",
      "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?w=600&q=80"
    ],
    earbuds: [
      "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&q=80",
      "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&q=80",
      "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600&q=80",
      "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=600&q=80"
    ],
    headphone: [
      "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
      "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&q=80",
      "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&q=80",
      "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&q=80"
    ],
    tablet: [
      "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&q=80",
      "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&q=80",
      "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?w=600&q=80",
      "https://images.unsplash.com/photo-1512499617640-c74ae3a79d37?w=600&q=80"
    ],
    monitor: [
      "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&q=80",
      "https://images.unsplash.com/photo-1585792180666-f7347c490ee2?w=600&q=80",
      "https://images.unsplash.com/photo-1547658719-da2b51169166?w=600&q=80",
      "https://images.unsplash.com/photo-1551645120-d70bfe84c826?w=600&q=80"
    ],
    keyboard: [
      "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&q=80",
      "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=600&q=80",
      "https://images.unsplash.com/photo-1595225476474-87563907a212?w=600&q=80",
      "https://images.unsplash.com/photo-1561152820-34078fbc37c7?w=600&q=80"
    ],
    mouse: [
      "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&q=80",
      "https://images.unsplash.com/photo-1626218174358-7769486c4b79?w=600&q=80",
      "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&q=80",
      "https://images.unsplash.com/photo-1605774330484-7d4560037f54?w=600&q=80"
    ],
    shoes: [
      "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
      "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80",
      "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=600&q=80",
      "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=600&q=80"
    ],
    gaming: [
      "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=600&q=80",
      "https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=600&q=80",
      "https://images.unsplash.com/photo-1621259182978-fbf93132d53d?w=600&q=80",
      "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?w=600&q=80"
    ]
  };

  let chosenCategory = "headphone";

  if (q.includes("iphone") || q.includes("phone") || q.includes("galaxy") || q.includes("pixel") || q.includes("mobile") || q.includes("smartphone")) {
    chosenCategory = "phone";
  } else if (q.includes("macbook") || q.includes("laptop") || q.includes("thinkpad") || q.includes("notebook") || q.includes("computer")) {
    chosenCategory = "laptop";
  } else if (q.includes("watch") || q.includes("smartwatch") || q.includes("rolex") || q.includes("band")) {
    chosenCategory = "watch";
  } else if (q.includes("camera") || q.includes("dslr") || q.includes("sony alpha") || q.includes("canon") || q.includes("nikon") || q.includes("lens")) {
    chosenCategory = "camera";
  } else if (q.includes("airpod") || q.includes("earbud") || q.includes("buds") || q.includes("in-ear") || q.includes("tws")) {
    chosenCategory = "earbuds";
  } else if (q.includes("ipad") || q.includes("tablet") || q.includes("surface pro")) {
    chosenCategory = "tablet";
  } else if (q.includes("monitor") || q.includes("display") || q.includes("screen") || q.includes("ultrasharp") || q.includes("tv")) {
    chosenCategory = "monitor";
  } else if (q.includes("keyboard") || q.includes("keychron") || q.includes("mechanical")) {
    chosenCategory = "keyboard";
  } else if (q.includes("mouse") || q.includes("mx master") || q.includes("trackpad") || q.includes("logitech mx")) {
    chosenCategory = "mouse";
  } else if (q.includes("shoe") || q.includes("sneaker") || q.includes("nike") || q.includes("adidas") || q.includes("jordan")) {
    chosenCategory = "shoes";
  } else if (q.includes("ps5") || q.includes("playstation") || q.includes("xbox") || q.includes("nintendo") || q.includes("gaming") || q.includes("console")) {
    chosenCategory = "gaming";
  } else if (q.includes("headphone") || q.includes("wh-1000") || q.includes("bose qc") || q.includes("anc") || q.includes("audio")) {
    chosenCategory = "headphone";
  }

  const list = catalog[chosenCategory];
  return list[index % list.length];
}

function generateDynamicSearchResults(query, brand, budget) {
  currentProductsList = [
    {
      id: "prod-dyn-1",
      name: `${query} — Pro Edition`,
      brand: brand || "Primary Brand",
      merchant: "ElectroDirect",
      price: roundPrice(budget * 0.95),
      rating: 4.9,
      avail: "In Stock & Ready",
      url: "#",
      img: resolveProductImage(query, brand, 0)
    },
    {
      id: "prod-dyn-2",
      name: `${query} — Retail Box`,
      brand: brand || "Primary Brand",
      merchant: "SoundHut",
      price: roundPrice(budget * 0.91),
      rating: 4.7,
      avail: "2-Day Shipping",
      url: "#",
      img: resolveProductImage(query, brand, 1)
    },
    {
      id: "prod-dyn-3",
      name: `${query} — Authorized Certified`,
      brand: brand || "Primary Brand",
      merchant: "BestBuy",
      price: roundPrice(budget * 1.04),
      rating: 4.8,
      avail: "Store Pickup Available",
      url: "#",
      img: resolveProductImage(query, brand, 2)
    },
    {
      id: "prod-dyn-4",
      name: `${query} — Studio Bundle`,
      brand: brand || "Primary Brand",
      merchant: "B&H Photo",
      price: roundPrice(budget * 0.88),
      rating: 4.5,
      avail: "In Stock",
      url: "#",
      img: resolveProductImage(query, brand, 3)
    }
  ];
}

function roundPrice(val) {
  return Math.round(val * 100) / 100;
}

function renderProductGrid() {
  const container = document.getElementById('productGridContainer');
  if (!container) return;

  const sortFilter = document.getElementById('productSortFilter');
  const sortMode = sortFilter ? sortFilter.value : 'lowest';
  let items = [...currentProductsList];

  if (sortMode === 'lowest') {
    items.sort((a, b) => a.price - b.price);
  } else if (sortMode === 'rating') {
    items.sort((a, b) => b.rating - a.rating);
  }

  container.innerHTML = items.map(p => `
    <div class="product-card card-glow">
      <div class="product-img-wrapper">
        <img src="${p.img}" alt="${p.name}" onerror="this.src='https://placehold.co/240x180/162238/818CF8?text=Product+Image'">
        <span class="badge badge-indigo product-badge-corner"><i class="fa-solid fa-star"></i> ${p.rating}</span>
      </div>
      <div class="product-body">
        <div class="product-brand">${p.brand} &bull; ${p.merchant}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-sub-info">
          <i class="fa-solid fa-truck-fast"></i> ${p.avail} &bull; <a href="#" onclick="event.preventDefault()" class="merchant-link">View Sourced Store</a>
        </div>
        <div class="product-meta-row">
          <div class="product-price-orig">$${p.price.toFixed(2)}</div>
          <button class="btn btn-primary btn-sm" onclick="selectProductForNegotiation('${p.id}')">
            <i class="fa-solid fa-bolt"></i> Negotiate
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

async function selectProductForNegotiation(prodId) {
  const p = currentProductsList.find(x => x.id === prodId);
  if (p) {
    AppState.currentProduct.id = p.id;
    AppState.currentProduct.name = p.name;
    AppState.currentProduct.brand = p.brand;
    AppState.currentProduct.merchant = p.merchant;
    AppState.currentProduct.originalPrice = p.price;
    AppState.currentProduct.targetPrice = roundPrice(p.price * 0.84);
    AppState.currentProduct.currentNegotiatedPrice = roundPrice(p.price * 0.88);
    AppState.currentProduct.savings = roundPrice(p.price - AppState.currentProduct.currentNegotiatedPrice);

    // Call backend API /api/negotiations/start
    try {
      const res = await ApiService.request('/negotiations/start', {
        method: 'POST',
        body: JSON.stringify({
          product_id: p.id,
          product_name: p.name,
          merchant_name: p.merchant,
          original_price: p.price,
          user_budget: p.price * 0.95
        })
      });

      if (res && res.id) {
        AppState.negotiationSession.id = res.id;
        if (res.offers && res.offers.length > 0) {
          AppState.negotiationSession.history = res.offers.map(o => ({
            sender: o.sender === 'AI_AGENT' ? 'ai' : 'merchant',
            text: o.message,
            time: new Date(o.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }));
        }
      }
    } catch (_) {}

    updateNegotiatorUI();
    renderNegotiationChat();
  }
  showToast(`Selected "${p.name}". Initializing Gemini agent deliberation...`, "success");
  switchView('negotiation');
}

/* =====================================================================
   6. SCREEN 3: PRODUCT COMPARISON (AG Grid Community)
   ===================================================================== */
let gridApi = null;

function initComparisonGrid() {
  const gridDiv = document.getElementById('comparisonGrid');
  if (!gridDiv) return;

  const columnDefs = [
    { field: "product", headerName: "Product", flex: 2, checkboxSelection: true, headerCheckboxSelection: true },
    { field: "merchant", headerName: "Merchant", flex: 1.2 },
    { 
      field: "originalPrice", 
      headerName: "Original Price", 
      flex: 1, 
      valueFormatter: params => `$${params.value.toFixed(2)}` 
    },
    { 
      field: "rating", 
      headerName: "Rating", 
      flex: 0.8,
      cellRenderer: params => `⭐ ${params.value}`
    },
    { field: "delivery", headerName: "Delivery Info", flex: 1.2 },
    { 
      field: "status", 
      headerName: "Negotiation Status", 
      flex: 1.5,
      cellRenderer: params => {
        const val = params.value;
        const color = val.includes('Negotiated') ? '#34D399' : (val.includes('Blocked') ? '#EF4444' : '#FBBF24');
        return `<span style="color: ${color}; font-weight:600;">${val}</span>`;
      }
    },
    { 
      field: "finalPrice", 
      headerName: "Final Price", 
      flex: 1,
      valueFormatter: params => `$${params.value.toFixed(2)}`
    },
    { 
      field: "savings", 
      headerName: "Savings", 
      flex: 1,
      cellRenderer: params => `<span style="color:#34D399; font-weight:700;">+$${params.value.toFixed(2)}</span>`
    }
  ];

  const gridOptions = {
    columnDefs: columnDefs,
    rowData: AppState.comparisonProducts,
    rowSelection: 'single',
    pagination: true,
    paginationPageSize: 8,
    defaultColDef: {
      sortable: true,
      filter: true,
      resizable: true
    }
  };

  gridApi = agGrid.createGrid(gridDiv, gridOptions);
}

function exportComparisonGridCsv() {
  if (gridApi) {
    gridApi.exportDataAsCsv({ fileName: 'dealpilot_comparison_matrix.csv' });
    showToast("Exported comparison matrix to CSV.", "info");
  }
}

function initiateNegotiationFromSelection() {
  if (!gridApi) return;
  const selectedNodes = gridApi.getSelectedNodes();
  if (selectedNodes.length === 0) {
    showToast("Please select a merchant row from the table first.", "warning");
    return;
  }
  const data = selectedNodes[0].data;
  if (!data.approved) {
    showToast("This merchant is not in your approved whitelist guardrail!", "danger");
    return;
  }
  AppState.currentProduct.name = data.product;
  AppState.currentProduct.merchant = data.merchant;
  AppState.currentProduct.originalPrice = data.originalPrice;
  updateNegotiatorUI();
  switchView('negotiation');
}

/* =====================================================================
   7. SCREEN 4: AI NEGOTIATION CENTER (Timeline & Bot Chat)
   ===================================================================== */
function updateNegotiatorUI() {
  const p = AppState.currentProduct;
  const sessionMerchant = document.getElementById('sessionMerchantName');
  if (sessionMerchant) sessionMerchant.textContent = `${p.merchant} Store`;

  document.getElementById('negoProductTitle').textContent = p.name;
  document.getElementById('negoOriginalPrice').textContent = `$${p.originalPrice.toFixed(2)}`;
  document.getElementById('negoTargetPrice').textContent = `$${p.targetPrice.toFixed(2)}`;
  document.getElementById('negoCurrentOffer').textContent = `$${p.currentNegotiatedPrice.toFixed(2)}`;
  
  const pct = Math.round((p.savings / p.originalPrice) * 100 * 10) / 10;
  document.getElementById('negoSavings').textContent = `$${p.savings.toFixed(2)} (${pct}%)`;

  // Update Screen 5 & 7 models
  document.getElementById('recTitle').textContent = p.name;
  document.getElementById('recMerchant').textContent = p.merchant + " Official";
  document.getElementById('recOriginalPrice').textContent = `$${p.originalPrice.toFixed(2)}`;
  document.getElementById('recFinalPrice').textContent = `$${p.currentNegotiatedPrice.toFixed(2)}`;
  document.getElementById('recSavings').textContent = `$${p.savings.toFixed(2)} (${pct}%)`;

  document.getElementById('checkoutProductTitle').textContent = p.name;
  document.getElementById('checkoutMerchantTitle').textContent = `Merchant: ${p.merchant}`;
  document.getElementById('checkoutOrigPrice').textContent = `$${p.originalPrice.toFixed(2)}`;
  document.getElementById('checkoutSubtotal').textContent = `$${p.currentNegotiatedPrice.toFixed(2)}`;
  
  const tax = Math.round(p.currentNegotiatedPrice * 0.06 * 100) / 100;
  document.getElementById('checkoutTax').textContent = `$${tax.toFixed(2)}`;
  document.getElementById('checkoutTotalAmount').textContent = `$${(p.currentNegotiatedPrice + tax).toFixed(2)}`;
}

function renderNegotiationChat() {
  const chatLog = document.getElementById('negotiationChatLog');
  if (!chatLog) return;

  chatLog.innerHTML = AppState.negotiationSession.history.map(msg => `
    <div class="chat-bubble ${msg.sender}">
      <div class="chat-bubble-author">
        ${msg.sender === 'ai' ? '<i class="fa-solid fa-robot"></i> DealPilot Agent' : '<i class="fa-solid fa-store"></i> Merchant API Endpoint'} &bull; ${msg.time}
      </div>
      <div>${msg.text}</div>
    </div>
  `).join('');

  chatLog.scrollTop = chatLog.scrollHeight;
}

async function simulateNextNegotiationStep() {
  const aiStatus = document.getElementById('aiStatusState');
  const stepCounter = document.getElementById('negoRoundCounter');

  aiStatus.textContent = "Synthesizing dynamic strategy...";

  // Call backend API /api/negotiations/{id}/counteroffer
  const result = await ApiService.request(`/negotiations/${AppState.negotiationSession.id}/counteroffer`, {
    method: 'POST',
    body: JSON.stringify({ counter_amount: AppState.currentProduct.currentNegotiatedPrice, strategy: "volume_rebate" })
  });

  const targetAmount = result.responsePrice || AppState.currentProduct.currentNegotiatedPrice;

  // Add agent counteroffer
  setTimeout(() => {
    AppState.negotiationSession.history.push({
      sender: "ai",
      text: `Deliberation iteration 3: Sourced bulk competitor pricing. Requesting final authorization price of $${targetAmount.toFixed(2)}.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    renderNegotiationChat();
    aiStatus.textContent = "Awaiting merchant reply...";

    // Add merchant concession
    setTimeout(() => {
      AppState.negotiationSession.history.push({
        sender: "merchant",
        text: `Merchant conceded: Agreed to lock price at $${targetAmount.toFixed(2)} with express shipping. Voucher token #VP-882 valid for 1 hour.`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
      renderNegotiationChat();
      aiStatus.textContent = "Deal Locked & Ready";
      if (stepCounter) stepCounter.textContent = "Round 3 / 3 (Accepted)";
      
      // Light up timeline step 5
      const step5Dot = document.getElementById('timelineStep5Dot');
      const step5Text = document.getElementById('timelineStep5Text');
      if (step5Dot) {
        step5Dot.style.background = "#10B981";
        step5Dot.style.color = "#fff";
        step5Dot.style.borderColor = "#10B981";
        step5Dot.style.boxShadow = "0 0 16px rgba(16, 185, 129, 0.4)";
      }
      if (step5Text) {
        step5Text.style.color = "#34D399";
        step5Text.style.fontWeight = "700";
      }
      showToast(`Merchant accepted negotiated price of $${targetAmount.toFixed(2)}!`, "success");
    }, 1200);
  }, 800);
}

function sendUserPromptToAI() {
  const input = document.getElementById('manualOverrideInput');
  const text = input.value.trim();
  if (!text) return;

  AppState.negotiationSession.history.push({
    sender: "ai",
    text: `[User Guideline Received]: "${text}". Adjusting algorithm aggression accordingly.`,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });
  input.value = '';
  renderNegotiationChat();
}

function resetNegotiationSimulation() {
  AppState.negotiationSession.history = [
    { sender: "ai", text: "Product 'Sony WH-1000XM4' indexed. Target set: $230.00.", time: "10:14 AM" },
    { sender: "ai", text: "Offer dispatched to ElectroDirect merchant: $225.00.", time: "10:15 AM" },
    { sender: "merchant", text: "Merchant Response: We can do $245.00 with free express shipping.", time: "10:16 AM" }
  ];
  renderNegotiationChat();
  const stepCounter = document.getElementById('negoRoundCounter');
  if (stepCounter) stepCounter.textContent = "Round 1 / 3";
  document.getElementById('aiStatusState').textContent = "AI Strategy Active";
  showToast("Negotiation session reset.", "info");
}

/* =====================================================================
   8. SCREEN 5: BEST DEAL RECOMMENDATION
   ===================================================================== */
async function approveAndProceedToCheckout() {
  showToast("Approving deal with backend security...", "info");
  
  // Call backend API /api/purchases/approve
  await ApiService.request('/purchases/approve', {
    method: 'POST',
    body: JSON.stringify({
      negotiation_id: AppState.negotiationSession.id,
      productId: AppState.currentProduct.id,
      finalPrice: AppState.currentProduct.currentNegotiatedPrice,
      merchant: AppState.currentProduct.merchant
    })
  });

  showToast("Deal approved. Proceeding to PayPal Sandbox checkout.", "success");
  switchView('checkout');
}

function rejectCurrentOffer() {
  showToast("Offer rejected. Resetting target heuristics.", "warning");
  switchView('search');
}

/* =====================================================================
   9. SCREEN 6: SPENDING GUARDRAILS LOGIC
   ===================================================================== */
async function savePolicySettings() {
  const maxBudget = parseFloat(document.getElementById('policyMaxBudget').value);
  const threshold = parseFloat(document.getElementById('policyApprovalThreshold').value);
  const rounds = parseInt(document.getElementById('policyMaxRounds').value);

  AppState.userPolicies.maxBudget = maxBudget;
  AppState.userPolicies.approvalThreshold = threshold;
  AppState.userPolicies.maxRounds = rounds;

  const dashBudget = document.getElementById('dashGuardrailBudget');
  if (dashBudget) dashBudget.textContent = `$${maxBudget.toFixed(2)}`;

  // Sync with backend API PUT /api/policies
  await ApiService.request('/policies', {
    method: 'PUT',
    body: JSON.stringify({
      max_spending_budget: maxBudget,
      approval_threshold: threshold,
      max_negotiation_attempts: rounds,
      approved_merchants: AppState.userPolicies.approvedMerchants
    })
  });

  showToast("Safety guardrails updated & synced with backend policy engine.", "success");
}

function addWhitelistMerchant() {
  const input = document.getElementById('newWhitelistInput');
  const val = input.value.trim();
  if (!val) return;

  if (!AppState.userPolicies.approvedMerchants.includes(val)) {
    AppState.userPolicies.approvedMerchants.push(val);
    renderWhitelistTags();
    input.value = '';
    showToast(`Added ${val} to verified whitelist.`, "success");
  }
}

function removeWhitelist(storeName) {
  AppState.userPolicies.approvedMerchants = AppState.userPolicies.approvedMerchants.filter(s => s !== storeName);
  renderWhitelistTags();
  showToast(`Removed ${storeName} from whitelist.`, "warning");
}

function renderWhitelistTags() {
  const container = document.getElementById('whitelistTagContainer');
  if (!container) return;
  container.innerHTML = AppState.userPolicies.approvedMerchants.map(m => `
    <span class="badge badge-indigo">
      ${m} <i class="fa-solid fa-xmark tag-close" onclick="removeWhitelist('${m}')"></i>
    </span>
  `).join('');
}

/* =====================================================================
   10. SCREEN 7: PAYPAL CHECKOUT (Backend SDK Order Flow)
   ===================================================================== */
async function executePayPalSandboxOrderFlow() {
  const actionArea = document.getElementById('paypalActionArea');
  const banner = document.getElementById('checkoutSuccessBanner');
  
  showToast("Requesting PayPal order token from backend...", "info");

  // 1. Create order token via backend API POST /api/payments/create-order
  const order = await ApiService.request('/payments/create-order', {
    method: 'POST',
    body: JSON.stringify({
      negotiation_id: AppState.negotiationSession.id,
      amount: AppState.currentProduct.currentNegotiatedPrice,
      currency: "USD"
    })
  });

  const orderId = order.order_id || order.id || ("PAYPAL-ORD-" + Math.floor(Math.random() * 899999 + 100000));
  showToast(`Order token created: ${orderId}. Capturing payment...`, "info");

  // 2. Capture payment via backend API POST /api/payments/capture-order
  setTimeout(async () => {
    const capture = await ApiService.request('/payments/capture-order', {
      method: 'POST',
      body: JSON.stringify({
        negotiation_id: AppState.negotiationSession.id,
        paypal_order_id: orderId
      })
    });

    const capId = capture.capture_id || capture.captureId || ("CAP-" + Math.floor(Math.random() * 899999 + 100000));

    actionArea.style.display = 'none';
    banner.style.display = 'block';
    document.getElementById('checkoutTransactionMeta').innerHTML = 
      `Capture ID: <strong>${capId}</strong> &bull; Order: <strong>${orderId}</strong> &bull; Settlement: <strong>COMPLETED (Sandbox)</strong>`;
    
    // Add to ledger
    AppState.transactionsLedger.unshift({
      id: capId,
      product: AppState.currentProduct.name,
      merchant: AppState.currentProduct.merchant,
      origPrice: AppState.currentProduct.originalPrice,
      finalPrice: AppState.currentProduct.currentNegotiatedPrice,
      savings: AppState.currentProduct.savings,
      status: "COMPLETED",
      date: new Date().toISOString().split('T')[0]
    });

    if (analyticsGridApi) {
      analyticsGridApi.setGridOption('rowData', AppState.transactionsLedger);
    }

    showToast("Payment successfully settled via PayPal Sandbox!", "success");
  }, 1200);
}

/* =====================================================================
   11. SCREEN 8: ANALYTICS DASHBOARD (Chart.js + AG Grid)
   ===================================================================== */
let analyticsGridApi = null;
let monthlyChart = null;
let merchantChart = null;

function renderAnalyticsCharts() {
  // Monthly Chart
  const ctxMonthly = document.getElementById('monthlySavingsChart');
  if (ctxMonthly) {
    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(ctxMonthly, {
      type: 'line',
      data: {
        labels: ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
        datasets: [
          {
            label: 'Savings ($)',
            data: [120, 240, 310, 480, 720, 1428],
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            tension: 0.35,
            fill: true
          },
          {
            label: 'Total Spend ($)',
            data: [450, 890, 1100, 1600, 2200, 3100],
            borderColor: '#6366F1',
            backgroundColor: 'rgba(99, 102, 241, 0.06)',
            tension: 0.35,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94A3B8', font: { family: 'Inter', size: 12 } } }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#64748B' } },
          y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#64748B' } }
        }
      }
    });
  }

  // Merchant Pie/Bar Chart
  const ctxMerchant = document.getElementById('merchantComparisonChart');
  if (ctxMerchant) {
    if (merchantChart) merchantChart.destroy();
    merchantChart = new Chart(ctxMerchant, {
      type: 'bar',
      data: {
        labels: ['ElectroDirect', 'SoundHut', 'BestBuy', 'Amazon', 'B&H Photo'],
        datasets: [{
          label: 'Successful Discounts Won',
          data: [14, 9, 7, 5, 3],
          backgroundColor: ['#6366F1', '#8B5CF6', '#EC4899', '#3B82F6', '#10B981'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748B' } },
          y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#64748B' } }
        }
      }
    });
  }
}

function initAnalyticsGrid() {
  const gridDiv = document.getElementById('analyticsTransactionsGrid');
  if (!gridDiv) return;

  const columnDefs = [
    { field: "id", headerName: "Transaction ID", flex: 1.2 },
    { field: "product", headerName: "Product", flex: 2 },
    { field: "merchant", headerName: "Merchant", flex: 1.2 },
    { field: "origPrice", headerName: "Original", flex: 1, valueFormatter: p => `$${p.value.toFixed(2)}` },
    { field: "finalPrice", headerName: "Captured", flex: 1, valueFormatter: p => `$${p.value.toFixed(2)}` },
    { field: "savings", headerName: "Savings", flex: 1, cellRenderer: p => `<span style="color:#34D399; font-weight:700;">+$${p.value.toFixed(2)}</span>` },
    { 
      field: "status", 
      headerName: "Payment Status", 
      flex: 1.2,
      cellRenderer: p => `<span class="badge badge-success">${p.value}</span>`
    },
    { field: "date", headerName: "Timestamp", flex: 1 }
  ];

  const gridOptions = {
    columnDefs: columnDefs,
    rowData: AppState.transactionsLedger,
    pagination: true,
    paginationPageSize: 5,
    defaultColDef: {
      sortable: true,
      filter: true,
      resizable: true
    }
  };

  analyticsGridApi = agGrid.createGrid(gridDiv, gridOptions);
}

function exportTransactionLedgerCsv() {
  if (analyticsGridApi) {
    analyticsGridApi.exportDataAsCsv({ fileName: 'dealpilot_transactions_ledger.csv' });
    showToast("Exported transaction audit ledger to CSV.", "info");
  }
}

/* =====================================================================
   12. SCREEN 9: NOTIFICATIONS & TOAST SYSTEM
   ===================================================================== */
function openNotificationsModal() {
  renderNotificationList();
  document.getElementById('notificationsModal').classList.add('active');
}

function closeNotificationsModal(e) {
  if (e && e.target !== e.currentTarget && e.currentTarget.id !== 'notificationsModal') return;
  document.getElementById('notificationsModal').classList.remove('active');
}

function renderNotificationList() {
  const body = document.getElementById('notificationListBody');
  if (!body) return;

  body.innerHTML = AppState.notifications.map(n => `
    <div class="notification-item ${n.unread ? 'unread' : ''}">
      <div style="font-size: 1.3rem; color:${n.type === 'success' ? '#34D399' : (n.type === 'warning' ? '#FBBF24' : '#818CF8')};">
        <i class="fa-solid fa-${n.type === 'success' ? 'circle-check' : (n.type === 'warning' ? 'triangle-exclamation' : 'circle-info')}"></i>
      </div>
      <div style="flex:1;">
        <div style="display:flex; justify-content:space-between;">
          <span style="font-weight:600; color:#fff; font-size:0.88rem;">${n.title}</span>
          <span style="font-size:0.72rem; color:var(--text-subtle);">${n.time}</span>
        </div>
        <div style="font-size:0.82rem; color:var(--text-muted); margin-top:3px;">${n.desc}</div>
      </div>
    </div>
  `).join('');
}

function markAllNotificationsRead() {
  AppState.notifications.forEach(n => n.unread = false);
  const count = document.getElementById('unreadNotifCount');
  if (count) count.textContent = '0';
  renderNotificationList();
  showToast("All notifications marked as read.", "info");
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast-pill';

  let icon = 'circle-info';
  let iconColor = '#818CF8';
  if (type === 'success') { icon = 'circle-check'; iconColor = '#34D399'; }
  if (type === 'warning') { icon = 'triangle-exclamation'; iconColor = '#FBBF24'; }
  if (type === 'danger') { icon = 'circle-exclamation'; iconColor = '#EF4444'; }

  toast.innerHTML = `
    <i class="fa-solid fa-${icon}" style="color: ${iconColor};"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* =====================================================================
   13. APPLICATION INITIALIZATION LIFECYCLE
   ===================================================================== */
window.addEventListener('DOMContentLoaded', async () => {
  // 1. Setup navigation hooks
  initNavigation();

  // 2. Render initial dashboard session lists & default product grid
  renderDashboardRecentList();
  renderProductGrid();

  // 3. Initialize AG Grids
  initComparisonGrid();
  initAnalyticsGrid();

  // 4. Render negotiation logs
  renderNegotiationChat();
  updateNegotiatorUI();

  // 5. Check FastAPI backend health endpoint
  try {
    const health = await ApiService.request('/health');
    if (health && (health.status === "ok" || health.status === "healthy")) {
      setBackendOnlineState(true);
    }
  } catch (e) {
    setBackendOnlineState(false);
  }
});
