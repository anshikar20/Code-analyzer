/**
 * Enterprise Inventory & ERP System — CodePulse AI Sample File
 * Language: Java 17 (Spring Boot style)
 * Lines: ~1550 | Contains: null pointer risks, raw types, resource leaks,
 *         SQL injection, insecure deserialization, performance issues, dead code
 *
 * Architecture: Controller → Service → Repository → Entity
 */

package com.codepulse.enterprise.inventory;

import java.util.*;
import java.util.stream.*;
import java.util.concurrent.*;
import java.io.*;
import java.net.*;
import java.sql.*;
import java.time.*;
import java.time.format.*;
import java.math.*;
import java.security.*;
import java.nio.charset.*;
import java.util.logging.*;

// ─── Annotations (simulated — no Spring on classpath) ─────────────────────
@interface Entity {}
@interface Table { String name() default ""; }
@interface Column { String name() default ""; boolean nullable() default true; }
@interface Id {}
@interface GeneratedValue {}
@interface Repository {}
@interface Service {}
@interface RestController {}
@interface RequestMapping { String value() default ""; }
@interface GetMapping { String value() default ""; }
@interface PostMapping { String value() default ""; }
@interface PutMapping { String value() default ""; }
@interface DeleteMapping { String value() default ""; }
@interface RequestBody {}
@interface PathVariable {}
@interface RequestParam { String value() default ""; }
@interface Autowired {}
@interface Valid {}
@interface Transactional {}
@interface Cacheable { String value() default ""; }

// ════════════════════════════════════════════════════════════════════
// Constants — Security Issues
// ════════════════════════════════════════════════════════════════════
class AppConstants {
    // ❌ SECURITY: Hardcoded credentials
    public static final String DB_URL = "jdbc:postgresql://prod-db:5432/inventory";
    public static final String DB_USER = "admin";
    public static final String DB_PASSWORD = "Pr0d_P@ssw0rd_2024!";
    public static final String JWT_SECRET = "myJwtSecretKey123456789_hardcoded";
    public static final String ENCRYPTION_KEY = "AES_KEY_1234567890123456";
    public static final String ADMIN_DEFAULT_PASSWORD = "Admin@123";

    public static final int MAX_RETRY_ATTEMPTS = 3;
    public static final int DEFAULT_PAGE_SIZE = 50;
    public static final long SESSION_TIMEOUT_MS = 86_400_000L; // 24h
}

// ════════════════════════════════════════════════════════════════════
// Enumerations
// ════════════════════════════════════════════════════════════════════
enum ProductStatus { ACTIVE, INACTIVE, DISCONTINUED, PENDING_REVIEW }
enum OrderStatus  { DRAFT, SUBMITTED, APPROVED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED }
enum UserRole     { SUPER_ADMIN, ADMIN, MANAGER, STAFF, VIEWER }
enum StockMovementType { RECEIPT, ISSUE, TRANSFER, ADJUSTMENT, RETURN }
enum WarehouseZone { ZONE_A, ZONE_B, ZONE_C, COLD_STORAGE, HAZMAT }

// ════════════════════════════════════════════════════════════════════
// Domain Entities
// ════════════════════════════════════════════════════════════════════

@Entity
@Table(name = "products")
class Product {
    @Id @GeneratedValue
    private Long id;

    @Column(name = "sku", nullable = false)
    private String sku;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "description")
    private String description;

    @Column(name = "unit_price")
    private BigDecimal unitPrice;

    @Column(name = "cost_price")
    private BigDecimal costPrice;

    @Column(name = "quantity_on_hand")
    private Integer quantityOnHand;

    @Column(name = "reorder_level")
    private Integer reorderLevel;

    @Column(name = "status")
    private ProductStatus status;

    @Column(name = "category")
    private String category;

    @Column(name = "weight_kg")
    private Double weightKg;

    @Column(name = "dimensions")
    private String dimensions;

    @Column(name = "barcode")
    private String barcode;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "is_deleted")
    private Boolean isDeleted = false;

    // Constructors
    public Product() {}

    public Product(String sku, String name, BigDecimal unitPrice, Integer qty) {
        this.sku = sku;
        this.name = name;
        this.unitPrice = unitPrice;
        this.quantityOnHand = qty;
        this.status = ProductStatus.ACTIVE;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // Getters & Setters (abbreviated)
    public Long getId() { return id; }
    public String getSku() { return sku; }
    public String getName() { return name; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public Integer getQuantityOnHand() { return quantityOnHand; }
    public ProductStatus getStatus() { return status; }
    public Boolean getIsDeleted() { return isDeleted; }
    public String getCategory() { return category; }

    public void setId(Long id) { this.id = id; }
    public void setSku(String sku) { this.sku = sku; }
    public void setName(String name) { this.name = name; }
    public void setUnitPrice(BigDecimal price) { this.unitPrice = price; }
    public void setQuantityOnHand(Integer qty) { this.quantityOnHand = qty; }
    public void setStatus(ProductStatus status) { this.status = status; }
    public void setIsDeleted(Boolean deleted) { this.isDeleted = deleted; }
    public void setCategory(String category) { this.category = category; }
    public void setUpdatedAt(LocalDateTime dt) { this.updatedAt = dt; }

    public boolean isLowStock() {
        // ❌ QUALITY: NullPointerException risk if quantityOnHand or reorderLevel is null
        return quantityOnHand <= reorderLevel;
    }

    public BigDecimal getMargin() {
        if (costPrice == null || unitPrice == null) return BigDecimal.ZERO;
        return unitPrice.subtract(costPrice).divide(unitPrice, 4, RoundingMode.HALF_UP);
    }

    @Override
    public String toString() {
        return String.format("Product{id=%d, sku='%s', name='%s', qty=%d}", id, sku, name, quantityOnHand);
    }
}

@Entity
@Table(name = "users")
class User {
    @Id @GeneratedValue
    private Long id;
    private String username;
    private String email;
    private String passwordHash;
    private UserRole role;
    private Boolean isActive = true;
    private Integer failedLoginAttempts = 0;
    private LocalDateTime lastLogin;
    private LocalDateTime createdAt = LocalDateTime.now();

    public User() {}
    public User(String username, String email, String passwordHash, UserRole role) {
        this.username = username;
        this.email = email;
        this.passwordHash = passwordHash;
        this.role = role;
    }

    public Long getId() { return id; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getPasswordHash() { return passwordHash; }
    public UserRole getRole() { return role; }
    public Boolean isActive() { return isActive; }
    public Integer getFailedLoginAttempts() { return failedLoginAttempts; }

    public void setId(Long id) { this.id = id; }
    public void setPasswordHash(String hash) { this.passwordHash = hash; }
    public void setIsActive(Boolean active) { this.isActive = active; }
    public void setLastLogin(LocalDateTime dt) { this.lastLogin = dt; }
    public void setFailedLoginAttempts(Integer n) { this.failedLoginAttempts = n; }
}

@Entity
@Table(name = "purchase_orders")
class PurchaseOrder {
    @Id @GeneratedValue
    private Long id;
    private Long supplierId;
    private Long createdByUserId;
    private OrderStatus status = OrderStatus.DRAFT;
    private LocalDateTime orderDate;
    private LocalDateTime expectedDelivery;
    private BigDecimal totalAmount = BigDecimal.ZERO;
    private String notes;
    private List<PurchaseOrderLine> lines = new ArrayList<>();

    public PurchaseOrder() {}
    public Long getId() { return id; }
    public List<PurchaseOrderLine> getLines() { return lines; }
    public OrderStatus getStatus() { return status; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setId(Long id) { this.id = id; }
    public void setStatus(OrderStatus s) { this.status = s; }
    public void addLine(PurchaseOrderLine line) { lines.add(line); }

    public void recalculateTotal() {
        this.totalAmount = lines.stream()
            .map(l -> l.getUnitCost().multiply(new BigDecimal(l.getQuantityOrdered())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}

class PurchaseOrderLine {
    private Long id;
    private Long productId;
    private Integer quantityOrdered;
    private Integer quantityReceived = 0;
    private BigDecimal unitCost;

    public PurchaseOrderLine() {}
    public PurchaseOrderLine(Long productId, Integer qty, BigDecimal cost) {
        this.productId = productId;
        this.quantityOrdered = qty;
        this.unitCost = cost;
    }

    public Long getProductId() { return productId; }
    public Integer getQuantityOrdered() { return quantityOrdered; }
    public Integer getQuantityReceived() { return quantityReceived; }
    public BigDecimal getUnitCost() { return unitCost; }
    public void setQuantityReceived(Integer qty) { this.quantityReceived = qty; }
}

// ════════════════════════════════════════════════════════════════════
// DTOs
// ════════════════════════════════════════════════════════════════════
class ProductDTO {
    public Long id;
    public String sku;
    public String name;
    public String description;
    public BigDecimal unitPrice;
    public Integer quantityOnHand;
    public String status;
    public String category;

    public static ProductDTO fromEntity(Product p) {
        ProductDTO dto = new ProductDTO();
        dto.id = p.getId();
        dto.sku = p.getSku();
        dto.name = p.getName();
        dto.unitPrice = p.getUnitPrice();
        dto.quantityOnHand = p.getQuantityOnHand();
        dto.status = p.getStatus().name();
        dto.category = p.getCategory();
        return dto;
    }
}

class CreateProductRequest {
    public String sku;
    public String name;
    public String description;
    public BigDecimal unitPrice;
    public BigDecimal costPrice;
    public Integer initialStock;
    public Integer reorderLevel;
    public String category;
    public Double weightKg;

    public void validate() {
        // ❌ QUALITY: Minimal validation — no regex on SKU, no negative price check
        if (sku == null || sku.isEmpty()) throw new IllegalArgumentException("SKU is required");
        if (name == null || name.isEmpty()) throw new IllegalArgumentException("Name is required");
        if (unitPrice == null) throw new IllegalArgumentException("Price is required");
    }
}

class LoginRequest {
    public String username;
    public String password;
}

class LoginResponse {
    public String token;
    public String username;
    public String role;
    public Long expiresAt;
}

class PagedResponse<T> {
    public List<T> data;
    public int page;
    public int pageSize;
    public long total;
    public int totalPages;

    public PagedResponse(List<T> data, int page, int pageSize, long total) {
        this.data = data;
        this.page = page;
        this.pageSize = pageSize;
        this.total = total;
        this.totalPages = (int) Math.ceil((double) total / pageSize);
    }
}

// ════════════════════════════════════════════════════════════════════
// Repository Layer (raw JDBC — intentional vulnerabilities)
// ════════════════════════════════════════════════════════════════════
@Repository
class ProductRepository {
    private static final Logger log = Logger.getLogger(ProductRepository.class.getName());
    private Connection connection;

    public ProductRepository() {
        try {
            // ❌ QUALITY: Connection created once and never pooled or refreshed
            this.connection = DriverManager.getConnection(
                AppConstants.DB_URL, AppConstants.DB_USER, AppConstants.DB_PASSWORD
            );
        } catch (SQLException e) {
            log.severe("DB connection failed: " + e.getMessage());
        }
    }

    // ❌ SECURITY: SQL Injection via string concatenation
    public List<Product> searchByName(String name) {
        List<Product> results = new ArrayList<>();
        String sql = "SELECT * FROM products WHERE name LIKE '%" + name + "%' AND is_deleted = false";
        try {
            Statement stmt = connection.createStatement(); // ❌ Resource leak — not closed!
            ResultSet rs = stmt.executeQuery(sql);
            while (rs.next()) {
                results.add(mapRow(rs));
            }
        } catch (SQLException e) {
            log.warning("Search error: " + e.getMessage());
            // ❌ QUALITY: Exception swallowed
        }
        return results;
    }

    // ✅ SAFE: Parameterized query
    public Optional<Product> findById(Long id) {
        String sql = "SELECT * FROM products WHERE id = ? AND is_deleted = false";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, id);
            ResultSet rs = ps.executeQuery();
            if (rs.next()) return Optional.of(mapRow(rs));
        } catch (SQLException e) {
            log.warning("findById error: " + e.getMessage());
        }
        return Optional.empty();
    }

    public Optional<Product> findBySku(String sku) {
        try (PreparedStatement ps = connection.prepareStatement(
                "SELECT * FROM products WHERE sku = ? AND is_deleted = false")) {
            ps.setString(1, sku);
            ResultSet rs = ps.executeQuery();
            if (rs.next()) return Optional.of(mapRow(rs));
        } catch (SQLException e) {
            log.warning("findBySku error: " + e.getMessage());
        }
        return Optional.empty();
    }

    public Product save(Product p) {
        String sql = p.getId() == null
            ? "INSERT INTO products (sku, name, description, unit_price, cost_price, quantity_on_hand, reorder_level, status, category, created_at, updated_at, is_deleted) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
            : "UPDATE products SET name=?, description=?, unit_price=?, quantity_on_hand=?, status=?, category=?, updated_at=? WHERE id=?";

        try (PreparedStatement ps = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            if (p.getId() == null) {
                ps.setString(1, p.getSku());
                ps.setString(2, p.getName());
                ps.setString(3, "");
                ps.setBigDecimal(4, p.getUnitPrice());
                ps.setBigDecimal(5, BigDecimal.ZERO);
                ps.setInt(6, p.getQuantityOnHand() != null ? p.getQuantityOnHand() : 0);
                ps.setInt(7, 10);
                ps.setString(8, p.getStatus().name());
                ps.setString(9, p.getCategory() != null ? p.getCategory() : "");
                ps.setString(10, LocalDateTime.now().toString());
                ps.setString(11, LocalDateTime.now().toString());
                ps.setBoolean(12, false);
            } else {
                ps.setString(1, p.getName());
                ps.setString(2, "");
                ps.setBigDecimal(3, p.getUnitPrice());
                ps.setInt(4, p.getQuantityOnHand() != null ? p.getQuantityOnHand() : 0);
                ps.setString(5, p.getStatus().name());
                ps.setString(6, p.getCategory() != null ? p.getCategory() : "");
                ps.setString(7, LocalDateTime.now().toString());
                ps.setLong(8, p.getId());
            }
            ps.executeUpdate();
            if (p.getId() == null) {
                ResultSet generatedKeys = ps.getGeneratedKeys();
                if (generatedKeys.next()) p.setId(generatedKeys.getLong(1));
            }
        } catch (SQLException e) {
            throw new RuntimeException("Failed to save product", e);
        }
        return p;
    }

    // ❌ PERFORMANCE: Fetching ALL products into memory — no pagination
    public List<Product> findAll() {
        List<Product> results = new ArrayList<>();
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM products WHERE is_deleted = false")) {
            while (rs.next()) {
                results.add(mapRow(rs));
            }
        } catch (SQLException e) {
            log.severe("findAll error: " + e.getMessage());
        }
        return results;
    }

    public boolean softDelete(Long id) {
        try (PreparedStatement ps = connection.prepareStatement(
                "UPDATE products SET is_deleted = true WHERE id = ?")) {
            ps.setLong(1, id);
            return ps.executeUpdate() > 0;
        } catch (SQLException e) {
            log.warning("softDelete error: " + e.getMessage());
            return false;
        }
    }

    // ❌ SECURITY: SQL Injection in category filter
    public List<Product> findByCategory(String category) {
        List<Product> results = new ArrayList<>();
        String sql = "SELECT * FROM products WHERE category = '" + category + "' AND is_deleted = false";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) results.add(mapRow(rs));
        } catch (SQLException e) {
            log.warning("findByCategory error: " + e.getMessage());
        }
        return results;
    }

    private Product mapRow(ResultSet rs) throws SQLException {
        Product p = new Product();
        p.setId(rs.getLong("id"));
        p.setSku(rs.getString("sku"));
        p.setName(rs.getString("name"));
        p.setUnitPrice(rs.getBigDecimal("unit_price"));
        p.setQuantityOnHand(rs.getInt("quantity_on_hand"));
        p.setStatus(ProductStatus.valueOf(rs.getString("status")));
        p.setCategory(rs.getString("category"));
        p.setIsDeleted(rs.getBoolean("is_deleted"));
        return p;
    }
}

@Repository
class UserRepository {
    private Connection connection;
    private static final Logger log = Logger.getLogger(UserRepository.class.getName());

    public UserRepository() {
        try {
            this.connection = DriverManager.getConnection(
                AppConstants.DB_URL, AppConstants.DB_USER, AppConstants.DB_PASSWORD
            );
        } catch (SQLException e) {
            log.severe("DB connection failed: " + e.getMessage());
        }
    }

    // ❌ SECURITY: SQL Injection
    public Optional<User> findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        try {
            Statement stmt = connection.createStatement();
            ResultSet rs = stmt.executeQuery(sql);
            if (rs.next()) {
                User u = new User();
                u.setId(rs.getLong("id"));
                return Optional.of(u);
            }
        } catch (SQLException e) {
            log.warning("findByUsername: " + e.getMessage());
        }
        return Optional.empty();
    }

    public User save(User user) {
        // Implementation abbreviated for brevity
        return user;
    }

    public void updateFailedAttempts(Long userId, int attempts) {
        try (PreparedStatement ps = connection.prepareStatement(
                "UPDATE users SET failed_login_attempts = ? WHERE id = ?")) {
            ps.setInt(1, attempts);
            ps.setLong(2, userId);
            ps.executeUpdate();
        } catch (SQLException e) {
            log.warning("updateFailedAttempts: " + e.getMessage());
        }
    }
}

// ════════════════════════════════════════════════════════════════════
// Service Layer
// ════════════════════════════════════════════════════════════════════
@Service
class ProductService {
    private static final Logger log = Logger.getLogger(ProductService.class.getName());

    @Autowired
    private ProductRepository repository;

    // ❌ PERFORMANCE: No-TTL in-memory cache with no bound
    private final Map<Long, Product> cache = new ConcurrentHashMap<>();

    @Cacheable("products")
    public Optional<ProductDTO> getProductById(Long id) {
        if (cache.containsKey(id)) {
            return Optional.of(ProductDTO.fromEntity(cache.get(id)));
        }
        return repository.findById(id).map(p -> {
            cache.put(id, p);
            return ProductDTO.fromEntity(p);
        });
    }

    public ProductDTO createProduct(CreateProductRequest req) {
        req.validate();

        if (repository.findBySku(req.sku).isPresent()) {
            throw new IllegalArgumentException("SKU already exists: " + req.sku);
        }

        Product product = new Product(req.sku, req.name, req.unitPrice, req.initialStock != null ? req.initialStock : 0);
        product.setCategory(req.category);
        product = repository.save(product);
        cache.put(product.getId(), product);
        log.info("Product created: " + product.getSku());
        return ProductDTO.fromEntity(product);
    }

    @Transactional
    public ProductDTO updateProduct(Long id, CreateProductRequest req) {
        Product product = repository.findById(id)
            .orElseThrow(() -> new RuntimeException("Product not found: " + id));

        if (req.name != null) product.setName(req.name);
        if (req.unitPrice != null) product.setUnitPrice(req.unitPrice);
        if (req.category != null) product.setCategory(req.category);
        product.setUpdatedAt(LocalDateTime.now());

        product = repository.save(product);
        cache.put(id, product);
        return ProductDTO.fromEntity(product);
    }

    public void deleteProduct(Long id) {
        if (!repository.softDelete(id)) {
            throw new RuntimeException("Product not found or already deleted: " + id);
        }
        cache.remove(id);
    }

    // ❌ PERFORMANCE: Returns all products — no pagination support
    public List<ProductDTO> getAllProducts() {
        return repository.findAll().stream()
            .map(ProductDTO::fromEntity)
            .collect(Collectors.toList());
    }

    public List<ProductDTO> searchProducts(String query) {
        return repository.searchByName(query).stream()
            .map(ProductDTO::fromEntity)
            .collect(Collectors.toList());
    }

    public List<ProductDTO> getLowStockProducts() {
        return repository.findAll().stream() // ❌ PERFORMANCE: Loads ALL then filters
            .filter(p -> p.getQuantityOnHand() != null && p.getQuantityOnHand() <= 10)
            .map(ProductDTO::fromEntity)
            .collect(Collectors.toList());
    }

    public boolean adjustStock(Long productId, int delta) {
        Optional<Product> opt = repository.findById(productId);
        if (opt.isEmpty()) return false;
        Product p = opt.get();
        int newQty = p.getQuantityOnHand() + delta;
        if (newQty < 0) throw new IllegalArgumentException("Insufficient stock");
        p.setQuantityOnHand(newQty);
        repository.save(p);
        cache.put(productId, p);
        return true;
    }

    public Map<String, Object> getInventoryReport() {
        List<Product> all = repository.findAll(); // ❌ PERFORMANCE: Memory issue for large datasets
        long active = all.stream().filter(p -> p.getStatus() == ProductStatus.ACTIVE).count();
        long lowStock = all.stream().filter(Product::isLowStock).count(); // ❌ NPE risk
        BigDecimal totalValue = all.stream()
            .map(p -> p.getUnitPrice().multiply(new BigDecimal(p.getQuantityOnHand())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("totalProducts", all.size());
        report.put("activeProducts", active);
        report.put("lowStockProducts", lowStock);
        report.put("totalInventoryValue", totalValue);
        report.put("generatedAt", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        return report;
    }

    // ❌ DEAD CODE: This method is never called
    @Deprecated
    private List<Product> _legacyGetAllByRawQuery() {
        return repository.findAll();
    }
}

@Service
class AuthenticationService {
    private static final Logger log = Logger.getLogger(AuthenticationService.class.getName());
    private final Map<String, Map<String, Object>> activeSessions = new ConcurrentHashMap<>();

    @Autowired
    private UserRepository userRepo;

    // ❌ SECURITY: MD5 password hashing — use BCrypt!
    public String hashPassword(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] hash = md.digest(password.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    public LoginResponse login(String username, String password) {
        Optional<User> optUser = userRepo.findByUsername(username);
        if (optUser.isEmpty()) {
            log.warning("Login failed for unknown user: " + username);
            return null;
        }

        User user = optUser.get();
        if (!user.isActive()) throw new SecurityException("Account is deactivated");

        if (user.getFailedLoginAttempts() >= 5) {
            throw new SecurityException("Account locked due to too many failed attempts");
        }

        String hashedInput = hashPassword(password);
        if (!hashedInput.equals(user.getPasswordHash())) {
            userRepo.updateFailedAttempts(user.getId(), user.getFailedLoginAttempts() + 1);
            return null;
        }

        String token = generateToken(user);
        long expiresAt = System.currentTimeMillis() + AppConstants.SESSION_TIMEOUT_MS;

        Map<String, Object> session = new HashMap<>();
        session.put("userId", user.getId());
        session.put("username", user.getUsername());
        session.put("role", user.getRole().name());
        session.put("expiresAt", expiresAt);
        activeSessions.put(token, session);

        LoginResponse response = new LoginResponse();
        response.token = token;
        response.username = user.getUsername();
        response.role = user.getRole().name();
        response.expiresAt = expiresAt;

        userRepo.updateFailedAttempts(user.getId(), 0);
        return response;
    }

    // ❌ SECURITY: Weak token generation using MD5(username + timestamp)
    private String generateToken(User user) {
        try {
            String raw = user.getUsername() + ":" + System.currentTimeMillis() + ":" + AppConstants.JWT_SECRET;
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] hash = md.digest(raw.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    public Optional<Map<String, Object>> validateToken(String token) {
        Map<String, Object> session = activeSessions.get(token);
        if (session == null) return Optional.empty();
        long expiresAt = (Long) session.get("expiresAt");
        if (System.currentTimeMillis() > expiresAt) {
            activeSessions.remove(token);
            return Optional.empty();
        }
        return Optional.of(session);
    }

    public void logout(String token) {
        activeSessions.remove(token);
    }

    // ❌ DEAD CODE
    private int _countActiveSessions() { return activeSessions.size(); }
}

// ════════════════════════════════════════════════════════════════════
// REST Controllers
// ════════════════════════════════════════════════════════════════════
@RestController
@RequestMapping("/api/v1/products")
class ProductController {
    private static final Logger log = Logger.getLogger(ProductController.class.getName());

    @Autowired
    private ProductService productService;

    @Autowired
    private AuthenticationService authService;

    @GetMapping("")
    public Object getAllProducts(@RequestParam("page") int page, @RequestParam("size") int size,
                                 @RequestParam("search") String search) {
        try {
            List<ProductDTO> products;
            if (search != null && !search.isEmpty()) {
                products = productService.searchProducts(search);
            } else {
                products = productService.getAllProducts();
            }
            // ❌ QUALITY: Manual pagination in controller, should be in repository
            int start = (page - 1) * size;
            int end = Math.min(start + size, products.size());
            List<ProductDTO> page_data = products.subList(start, end);
            return new PagedResponse<>(page_data, page, size, products.size());
        } catch (Exception e) {
            log.severe("getAllProducts error: " + e.getMessage());
            return Map.of("error", e.getMessage(), "status", 500);
        }
    }

    @GetMapping("/{id}")
    public Object getProduct(@PathVariable Long id) {
        return productService.getProductById(id)
            .map(p -> (Object) p)
            .orElse(Map.of("error", "Not found", "status", 404));
    }

    @PostMapping("")
    public Object createProduct(@Valid @RequestBody CreateProductRequest request) {
        try {
            ProductDTO created = productService.createProduct(request);
            return Map.of("data", created, "status", 201);
        } catch (IllegalArgumentException e) {
            return Map.of("error", e.getMessage(), "status", 400);
        } catch (Exception e) {
            log.severe("createProduct error: " + e.getMessage());
            return Map.of("error", "Internal server error", "status", 500);
        }
    }

    @PutMapping("/{id}")
    public Object updateProduct(@PathVariable Long id, @RequestBody CreateProductRequest request) {
        try {
            return productService.updateProduct(id, request);
        } catch (RuntimeException e) {
            return Map.of("error", e.getMessage(), "status", 404);
        }
    }

    @DeleteMapping("/{id}")
    public Object deleteProduct(@PathVariable Long id) {
        try {
            productService.deleteProduct(id);
            return Map.of("message", "Product deleted", "status", 200);
        } catch (RuntimeException e) {
            return Map.of("error", e.getMessage(), "status", 404);
        }
    }

    @GetMapping("/report/inventory")
    public Object getInventoryReport() {
        return productService.getInventoryReport();
    }

    @GetMapping("/low-stock")
    public Object getLowStockProducts() {
        return productService.getLowStockProducts();
    }
}

@RestController
@RequestMapping("/api/v1/auth")
class AuthController {

    @Autowired
    private AuthenticationService authService;

    @PostMapping("/login")
    public Object login(@RequestBody LoginRequest request) {
        // ❌ QUALITY: No input validation before calling service
        LoginResponse response = authService.login(request.username, request.password);
        if (response == null) {
            return Map.of("error", "Invalid credentials", "status", 401);
        }
        return response;
    }

    @PostMapping("/logout")
    public Object logout(@RequestParam("token") String token) {
        authService.logout(token);
        return Map.of("message", "Logged out successfully");
    }

    @GetMapping("/validate")
    public Object validateToken(@RequestParam("token") String token) {
        return authService.validateToken(token)
            .map(session -> (Object) Map.of("valid", true, "session", session))
            .orElse(Map.of("valid", false));
    }
}

// ════════════════════════════════════════════════════════════════════
// Utility Classes
// ════════════════════════════════════════════════════════════════════
class StringUtils {
    private StringUtils() {}

    public static boolean isEmpty(String s) {
        return s == null || s.trim().isEmpty();
    }

    public static String truncate(String s, int maxLen) {
        if (s == null) return "";
        return s.length() > maxLen ? s.substring(0, maxLen) + "..." : s;
    }

    public static String capitalize(String s) {
        if (isEmpty(s)) return s;
        return Character.toUpperCase(s.charAt(0)) + s.substring(1).toLowerCase();
    }

    // ❌ DEAD CODE: Never used anywhere
    public static String reverseWords(String sentence) {
        if (isEmpty(sentence)) return sentence;
        String[] words = sentence.split("\\s+");
        StringBuilder result = new StringBuilder();
        for (int i = words.length - 1; i >= 0; i--) {
            result.append(words[i]);
            if (i > 0) result.append(" ");
        }
        return result.toString();
    }
}

class DateUtils {
    private static final DateTimeFormatter DISPLAY_FORMAT = DateTimeFormatter.ofPattern("dd MMM yyyy, HH:mm");
    private static final DateTimeFormatter ISO_FORMAT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    private DateUtils() {}

    public static String formatForDisplay(LocalDateTime dt) {
        if (dt == null) return "—";
        return dt.format(DISPLAY_FORMAT);
    }

    public static String toIso(LocalDateTime dt) {
        if (dt == null) return null;
        return dt.format(ISO_FORMAT);
    }

    public static boolean isExpired(LocalDateTime expiresAt) {
        return LocalDateTime.now().isAfter(expiresAt);
    }

    public static long daysBetween(LocalDateTime from, LocalDateTime to) {
        return java.time.temporal.ChronoUnit.DAYS.between(from, to);
    }
}

// ════════════════════════════════════════════════════════════════════
// Application Entry Point
// ════════════════════════════════════════════════════════════════════
public class EnterpriseInventoryApplication {
    private static final Logger log = Logger.getLogger(EnterpriseInventoryApplication.class.getName());

    public static void main(String[] args) {
        log.info("Starting CodePulse AI — Enterprise Inventory System v2.1.0");

        // Dependency setup (simulated DI)
        ProductRepository productRepo = new ProductRepository();
        UserRepository userRepo = new UserRepository();

        ProductService productService = new ProductService();
        AuthenticationService authService = new AuthenticationService();

        // Simulate some operations for testing
        CreateProductRequest req1 = new CreateProductRequest();
        req1.sku = "LAPTOP-001";
        req1.name = "ThinkPad X1 Carbon";
        req1.unitPrice = new BigDecimal("1299.99");
        req1.initialStock = 25;
        req1.category = "Electronics";

        CreateProductRequest req2 = new CreateProductRequest();
        req2.sku = "MOUSE-001";
        req2.name = "Logitech MX Master 3";
        req2.unitPrice = new BigDecimal("99.99");
        req2.initialStock = 150;
        req2.category = "Peripherals";

        log.info("Enterprise Inventory System initialized. Upload to CodePulse AI for analysis.");
    }
}
