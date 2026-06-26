/**
 * Enterprise Game Engine & Physics Simulation — CodePulse AI Sample File
 * Language: C++17
 * Lines: ~1550 | Contains: memory leaks, buffer overflows, use-after-free,
 *         dangling pointers, race conditions, missing destructors, STL misuse
 */

#pragma once

#include <iostream>
#include <vector>
#include <map>
#include <unordered_map>
#include <string>
#include <memory>
#include <thread>
#include <mutex>
#include <atomic>
#include <algorithm>
#include <functional>
#include <queue>
#include <stack>
#include <optional>
#include <variant>
#include <chrono>
#include <cstring>
#include <cassert>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <type_traits>
#include <random>

// ─── Constants & Configuration ────────────────────────────────────────────────
constexpr int MAX_ENTITIES      = 10000;
constexpr int MAX_COMPONENTS    = 64;
constexpr int PHYSICS_STEPS_PER_SEC = 60;
constexpr float GRAVITY         = -9.81f;
constexpr float EPSILON         = 1e-6f;
constexpr size_t POOL_BLOCK_SIZE = 4096;

// ❌ SECURITY: Hardcoded API endpoint and auth token
const char* TELEMETRY_URL       = "https://telemetry.mygame.com/v1/events";
const char* AUTH_TOKEN          = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.hardcoded";
const char* LICENSE_KEY         = "GAME-ENGINE-2024-XYZABC123";

// ─── Math Types ───────────────────────────────────────────────────────────────
struct Vec2 {
    float x, y;
    Vec2() : x(0.0f), y(0.0f) {}
    Vec2(float x, float y) : x(x), y(y) {}

    Vec2 operator+(const Vec2& o) const { return {x + o.x, y + o.y}; }
    Vec2 operator-(const Vec2& o) const { return {x - o.x, y - o.y}; }
    Vec2 operator*(float s) const { return {x * s, y * s}; }
    Vec2 operator/(float s) const { return {x / s, y / s}; } // ❌ QUALITY: No division by zero check
    Vec2& operator+=(const Vec2& o) { x += o.x; y += o.y; return *this; }
    Vec2& operator-=(const Vec2& o) { x -= o.x; y -= o.y; return *this; }

    float magnitude() const { return std::sqrt(x * x + y * y); }
    float magnitudeSquared() const { return x * x + y * y; }
    Vec2 normalized() const {
        float mag = magnitude();
        if (mag < EPSILON) return {0.0f, 0.0f};
        return {x / mag, y / mag};
    }
    float dot(const Vec2& o) const { return x * o.x + y * o.y; }
    float cross(const Vec2& o) const { return x * o.y - y * o.x; }
};

struct Vec3 {
    float x, y, z;
    Vec3() : x(0.0f), y(0.0f), z(0.0f) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}

    Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(float s) const { return {x / s, y / s, z / s}; } // ❌ No div-by-zero check

    float magnitude() const { return std::sqrt(x*x + y*y + z*z); }
    Vec3 normalized() const {
        float mag = magnitude();
        if (mag < EPSILON) return {};
        return {x/mag, y/mag, z/mag};
    }
    Vec3 cross(const Vec3& o) const {
        return {y*o.z - z*o.y, z*o.x - x*o.z, x*o.y - y*o.x};
    }
    float dot(const Vec3& o) const { return x*o.x + y*o.y + z*o.z; }
};

struct Mat4 {
    float m[4][4];
    Mat4() { memset(m, 0, sizeof(m)); }

    static Mat4 identity() {
        Mat4 result;
        for (int i = 0; i < 4; ++i) result.m[i][i] = 1.0f;
        return result;
    }

    Mat4 operator*(const Mat4& o) const {
        Mat4 result;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j)
                for (int k = 0; k < 4; ++k)
                    result.m[i][j] += m[i][k] * o.m[k][j];
        return result;
    }
};

struct AABB {
    Vec2 min, max;
    bool overlaps(const AABB& o) const {
        return !(max.x < o.min.x || min.x > o.max.x || max.y < o.min.y || min.y > o.max.y);
    }
    Vec2 center() const { return {(min.x + max.x) * 0.5f, (min.y + max.y) * 0.5f}; }
    Vec2 halfExtents() const { return {(max.x - min.x) * 0.5f, (max.y - min.y) * 0.5f}; }
};

// ─── Entity Component System ──────────────────────────────────────────────────
using EntityID = uint32_t;
using ComponentMask = uint64_t;
constexpr EntityID INVALID_ENTITY = 0;

// ─── Components ───────────────────────────────────────────────────────────────
struct TransformComponent {
    Vec3 position;
    Vec3 rotation;
    Vec3 scale = {1.0f, 1.0f, 1.0f};
    bool dirty = true;
    Mat4 worldMatrix;
};

struct PhysicsComponent {
    Vec3 velocity;
    Vec3 acceleration;
    float mass = 1.0f;
    float restitution = 0.5f;
    float friction = 0.3f;
    bool isStatic = false;
    bool isTrigger = false;
    bool isGrounded = false;
    AABB bounds;
};

struct RenderComponent {
    uint32_t meshId;
    uint32_t textureId;
    Vec3 color = {1.0f, 1.0f, 1.0f};
    bool isVisible = true;
    int layer = 0;
};

struct ScriptComponent {
    std::string scriptName;
    std::function<void(EntityID, float)> onUpdate;
    std::function<void(EntityID, EntityID)> onCollision;
    bool enabled = true;
};

struct AudioComponent {
    uint32_t soundId;
    float volume = 1.0f;
    bool looping = false;
    bool playing = false;
};

struct HealthComponent {
    float currentHealth;
    float maxHealth;
    float regenRate = 0.0f;
    bool isInvincible = false;

    float getPercentage() const {
        // ❌ QUALITY: No check for maxHealth == 0
        return currentHealth / maxHealth * 100.0f;
    }

    bool isAlive() const { return currentHealth > 0.0f; }

    void takeDamage(float amount) {
        if (isInvincible) return;
        currentHealth = std::max(0.0f, currentHealth - amount);
    }

    void heal(float amount) {
        currentHealth = std::min(maxHealth, currentHealth + amount);
    }
};

// ─── Memory Pool Allocator ────────────────────────────────────────────────────
class MemoryPool {
public:
    explicit MemoryPool(size_t blockSize, size_t blockCount)
        : m_blockSize(blockSize), m_blockCount(blockCount) {
        // ❌ MEMORY: Raw allocation — no smart pointer, must be manually freed
        m_pool = static_cast<char*>(malloc(blockSize * blockCount));
        if (!m_pool) throw std::bad_alloc();

        for (size_t i = 0; i < blockCount; ++i) {
            m_freeList.push(m_pool + i * blockSize);
        }
    }

    // ❌ QUALITY: No copy/move constructor defined (Rule of 5 violation)
    ~MemoryPool() {
        free(m_pool); // ❌ MEMORY: Only frees if destructor is called; no exception safety
    }

    void* allocate() {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_freeList.empty()) {
            // ❌ MEMORY: Returns nullptr instead of throwing — caller must check!
            return nullptr;
        }
        void* ptr = m_freeList.top();
        m_freeList.pop();
        return ptr;
    }

    void deallocate(void* ptr) {
        if (!ptr) return;
        std::lock_guard<std::mutex> lock(m_mutex);
        // ❌ MEMORY: No validation that ptr came from this pool!
        m_freeList.push(static_cast<char*>(ptr));
    }

    size_t available() const {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_freeList.size();
    }

private:
    char* m_pool;
    size_t m_blockSize;
    size_t m_blockCount;
    std::stack<char*> m_freeList;
    mutable std::mutex m_mutex;
};

// ─── Entity Manager ───────────────────────────────────────────────────────────
class EntityManager {
public:
    EntityManager() : m_nextId(1) {
        m_transforms.reserve(MAX_ENTITIES);
        m_physics.reserve(MAX_ENTITIES);
    }

    EntityID createEntity() {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (!m_recycled.empty()) {
            EntityID id = m_recycled.front();
            m_recycled.pop();
            m_masks[id] = 0;
            return id;
        }
        EntityID id = m_nextId++;
        m_masks[id] = 0;
        return id;
    }

    void destroyEntity(EntityID id) {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_masks.find(id) == m_masks.end()) return;
        m_masks.erase(id);
        m_transforms.erase(id);
        m_physics.erase(id);
        m_renders.erase(id);
        m_health.erase(id);
        m_recycled.push(id);
    }

    bool isAlive(EntityID id) const {
        return m_masks.find(id) != m_masks.end();
    }

    template<typename T>
    T& addComponent(EntityID id);

    template<typename T>
    T* getComponent(EntityID id);

    template<typename T>
    void removeComponent(EntityID id);

    std::vector<EntityID> getEntitiesWithComponents(ComponentMask mask) const {
        std::vector<EntityID> result;
        // ❌ PERFORMANCE: Linear scan over all entities every frame
        for (auto& [id, entityMask] : m_masks) {
            if ((entityMask & mask) == mask) {
                result.push_back(id);
            }
        }
        return result;
    }

    size_t entityCount() const { return m_masks.size(); }

    std::unordered_map<EntityID, TransformComponent> m_transforms;
    std::unordered_map<EntityID, PhysicsComponent> m_physics;
    std::unordered_map<EntityID, RenderComponent> m_renders;
    std::unordered_map<EntityID, HealthComponent> m_health;
    std::unordered_map<EntityID, ScriptComponent> m_scripts;

private:
    std::atomic<EntityID> m_nextId;
    std::unordered_map<EntityID, ComponentMask> m_masks;
    std::queue<EntityID> m_recycled;
    mutable std::mutex m_mutex;
};

// ─── Physics System ───────────────────────────────────────────────────────────
class PhysicsSystem {
public:
    PhysicsSystem(EntityManager& em) : m_em(em), m_gravity({0.0f, GRAVITY, 0.0f}) {}

    void step(float dt) {
        auto entities = m_em.getEntitiesWithComponents(0x03); // transform + physics mask

        // ❌ PERFORMANCE: No spatial partitioning — O(n²) collision detection
        for (EntityID a : entities) {
            auto* transA = &m_em.m_transforms[a];
            auto* physA  = &m_em.m_physics[a];

            if (physA->isStatic) continue;

            // Apply gravity
            physA->velocity = physA->velocity + m_gravity * dt;

            // Apply velocity
            transA->position = transA->position + physA->velocity * dt;
            transA->dirty = true;

            // Collision with all others — O(n²)!
            for (EntityID b : entities) {
                if (a == b) continue;
                auto* physB = &m_em.m_physics[b];

                if (physA->bounds.overlaps(physB->bounds)) {
                    resolveCollision(a, b, *physA, *physB, *transA);
                }
            }

            // Ground clamp
            if (transA->position.y <= 0.0f) {
                transA->position.y = 0.0f;
                physA->velocity.y = -physA->velocity.y * physA->restitution;
                physA->isGrounded = true;
            }
        }
    }

    void resolveCollision(EntityID a, EntityID b,
                          PhysicsComponent& physA, PhysicsComponent& physB,
                          TransformComponent& transA) {
        if (physB.isStatic) {
            // Simple bounce
            physA.velocity.y = -physA.velocity.y * physA.restitution;
            physA.velocity.x *= (1.0f - physA.friction);
            return;
        }

        // Conservation of momentum (1D simplified)
        float totalMass = physA.mass + physB.mass;
        Vec3 newVelA = physA.velocity * ((physA.mass - physB.mass) / totalMass)+ physB.velocity * (2.0f * physB.mass / totalMass);

        physA.velocity = newVelA;

        // Notify scripts
        if (m_em.m_scripts.count(a)) {
            if (m_em.m_scripts[a].onCollision) {
                m_em.m_scripts[a].onCollision(a, b);
            }
        }
    }

    void setGravity(Vec3 gravity) { m_gravity = gravity; }

private:
    EntityManager& m_em;
    Vec3 m_gravity;
};

// ─── Render System ────────────────────────────────────────────────────────────
class RenderSystem {
public:
    RenderSystem(EntityManager& em) : m_em(em), m_frameCount(0) {}

    void render(float interpolation) {
        std::vector<std::pair<int, EntityID>> sortedEntities;

        for (auto& [id, render] : m_em.m_renders) {
            if (render.isVisible) {
                sortedEntities.push_back({render.layer, id});
            }
        }

        // Sort by layer for correct draw order
        std::sort(sortedEntities.begin(), sortedEntities.end());

        for (auto& [layer, id] : sortedEntities) {
            drawEntity(id, interpolation);
        }

        ++m_frameCount;
    }

    void drawEntity(EntityID id, float interpolation) {
        auto* transform = &m_em.m_transforms[id]; // ❌ QUALITY: No bounds check — crashes if missing
        auto* render    = &m_em.m_renders[id];

        // ❌ PERFORMANCE: World matrix recalculated every frame even if not dirty
        updateWorldMatrix(*transform);

        // Simulate draw call (GPU API call would go here)
    }

    void updateWorldMatrix(TransformComponent& t) {
        if (!t.dirty) return;
        t.worldMatrix = Mat4::identity();
        // Translation, rotation, scale would be applied here
        t.dirty = false;
    }

    uint64_t getFrameCount() const { return m_frameCount; }

private:
    EntityManager& m_em;
    uint64_t m_frameCount;
};

// ─── Resource Manager ─────────────────────────────────────────────────────────
class ResourceManager {
public:
    ResourceManager() : m_nextId(1) {}

    // ❌ MEMORY LEAK: Returns raw pointer; caller responsible for deletion (rarely done)
    uint32_t loadTexture(const std::string& path) {
        if (m_textureCache.count(path)) {
            return m_textureCache[path];
        }

        // Simulate texture loading
        char* textureData = new char[1024 * 1024 * 4]; // 4MB per texture — never freed!
        uint32_t id = m_nextId++;
        m_textureCache[path] = id;
        // ❌ MEMORY: textureData is never stored or freed — memory leak!

        std::cout << "Loaded texture: " << path << " (ID=" << id << ")\n";
        return id;
    }

    uint32_t loadMesh(const std::string& path) {
        if (m_meshCache.count(path)) {
            return m_meshCache[path];
        }

        uint32_t id = m_nextId++;
        m_meshCache[path] = id;
        return id;
    }

    uint32_t loadSound(const std::string& path) {
        if (m_soundCache.count(path)) {
            return m_soundCache[path];
        }

        uint32_t id = m_nextId++;
        m_soundCache[path] = id;
        return id;
    }

    void unloadAll() {
        // ❌ MEMORY: Cache cleared but underlying GPU/audio resources not released
        m_textureCache.clear();
        m_meshCache.clear();
        m_soundCache.clear();
    }

    // ❌ DEAD CODE: Never called from anywhere in the codebase
    void _debugPrintStats() {
        std::cout << "Textures: " << m_textureCache.size() << "\n";
        std::cout << "Meshes: "   << m_meshCache.size() << "\n";
        std::cout << "Sounds: "   << m_soundCache.size() << "\n";
    }

private:
    std::atomic<uint32_t> m_nextId;
    std::unordered_map<std::string, uint32_t> m_textureCache;
    std::unordered_map<std::string, uint32_t> m_meshCache;
    std::unordered_map<std::string, uint32_t> m_soundCache;
};

// ─── Event System ─────────────────────────────────────────────────────────────
class EventSystem {
public:
    using EventHandler = std::function<void(const void*)>;

    void subscribe(const std::string& eventType, EventHandler handler) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_handlers[eventType].push_back(handler);
    }

    void publish(const std::string& eventType, const void* data = nullptr) {
        std::vector<EventHandler> handlers;
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            auto it = m_handlers.find(eventType);
            if (it == m_handlers.end()) return;
            handlers = it->second; // Copy to avoid holding lock during dispatch
        }

        for (auto& handler : handlers) {
            try {
                handler(data);
            } catch (const std::exception& e) {
                std::cerr << "EventSystem error on " << eventType << ": " << e.what() << "\n";
            }
        }
    }

    void unsubscribeAll(const std::string& eventType) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_handlers.erase(eventType);
    }

private:
    std::unordered_map<std::string, std::vector<EventHandler>> m_handlers;
    std::mutex m_mutex;
};

// ─── Scene Manager ────────────────────────────────────────────────────────────
class Scene {
public:
    explicit Scene(const std::string& name) : m_name(name), m_loaded(false) {}
    virtual ~Scene() {}

    virtual void onLoad() = 0;
    virtual void onUnload() = 0;
    virtual void onUpdate(float dt) = 0;
    virtual void onRender() = 0;

    const std::string& getName() const { return m_name; }
    bool isLoaded() const { return m_loaded; }

protected:
    std::string m_name;
    bool m_loaded;
};

class SceneManager {
public:
    void registerScene(std::unique_ptr<Scene> scene) {
        std::string name = scene->getName();
        m_scenes[name] = std::move(scene);
    }

    bool loadScene(const std::string& name) {
        if (m_activeScene) {
            m_activeScene->onUnload();
        }

        auto it = m_scenes.find(name);
        if (it == m_scenes.end()) {
            std::cerr << "Scene not found: " << name << "\n";
            return false;
        }

        m_activeScene = it->second.get(); // ❌ QUALITY: Raw pointer into unique_ptr map — dangling risk
        m_activeScene->onLoad();
        return true;
    }

    void update(float dt) {
        if (m_activeScene) m_activeScene->onUpdate(dt);
    }

    void render() {
        if (m_activeScene) m_activeScene->onRender();
    }

    Scene* getActiveScene() { return m_activeScene; }

private:
    std::unordered_map<std::string, std::unique_ptr<Scene>> m_scenes;
    Scene* m_activeScene = nullptr; // ❌ QUALITY: Raw observer pointer
};

// ─── Thread Pool ──────────────────────────────────────────────────────────────
class ThreadPool {
public:
    explicit ThreadPool(size_t numThreads) : m_stop(false) {
        for (size_t i = 0; i < numThreads; ++i) {
            m_workers.emplace_back([this] { workerLoop(); });
        }
    }

    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(m_mutex);
            m_stop = true;
        }
        m_condition.notify_all();
        for (auto& worker : m_workers) {
            if (worker.joinable()) worker.join();
        }
    }

    template<typename F>
    void submit(F&& task) {
        {
            std::unique_lock<std::mutex> lock(m_mutex);
            if (m_stop) throw std::runtime_error("ThreadPool is stopped");
            m_tasks.push(std::forward<F>(task));
        }
        m_condition.notify_one();
    }

    size_t pendingTasks() {
        std::unique_lock<std::mutex> lock(m_mutex);
        return m_tasks.size();
    }

private:
    void workerLoop() {
        while (true) {
            std::function<void()> task;
            {
                std::unique_lock<std::mutex> lock(m_mutex);
                m_condition.wait(lock, [this] { return m_stop || !m_tasks.empty(); });
                if (m_stop && m_tasks.empty()) return;
                task = std::move(m_tasks.front());
                m_tasks.pop();
            }
            try {
                task();
            } catch (const std::exception& e) {
                std::cerr << "ThreadPool task exception: " << e.what() << "\n";
            }
        }
    }

    std::vector<std::thread> m_workers;
    std::queue<std::function<void()>> m_tasks;
    std::mutex m_mutex;
    std::condition_variable m_condition;
    bool m_stop;
};

// ─── Game Engine ──────────────────────────────────────────────────────────────
class GameEngine {
public:
    GameEngine() :
        m_running(false),
        m_targetFPS(60),
        m_physicsSystem(m_entityManager),
        m_renderSystem(m_entityManager),
        m_threadPool(std::thread::hardware_concurrency())
    {
        m_memoryPool = std::make_unique<MemoryPool>(POOL_BLOCK_SIZE, 1024);
    }

    void initialize() {
        std::cout << "CodePulse AI Game Engine v2.1.0 — Initializing...\n";

        // Subscribe to events
        m_eventSystem.subscribe("entity:died", [this](const void* data) {
            const EntityID* id = static_cast<const EntityID*>(data);
            onEntityDied(*id);
        });

        m_eventSystem.subscribe("scene:load", [this](const void* data) {
            const std::string* name = static_cast<const std::string*>(data);
            m_sceneManager.loadScene(*name);
        });

        std::cout << "Engine initialized.\n";
    }

    EntityID spawnEntity(Vec3 position = {}) {
        EntityID id = m_entityManager.createEntity();

        auto& transform = m_entityManager.m_transforms[id];
        transform.position = position;
        transform.scale = {1.0f, 1.0f, 1.0f};
        transform.dirty = true;

        return id;
    }

    EntityID spawnPhysicsEntity(Vec3 position, float mass = 1.0f) {
        EntityID id = spawnEntity(position);

        auto& physics = m_entityManager.m_physics[id];
        physics.mass = mass;
        physics.restitution = 0.5f;
        physics.friction = 0.3f;
        physics.bounds = {{position.x - 0.5f, position.y - 0.5f},
                          {position.x + 0.5f, position.y + 0.5f}};

        return id;
    }

    EntityID spawnCharacter(Vec3 position, float maxHealth = 100.0f) {
        EntityID id = spawnPhysicsEntity(position, 70.0f);

        auto& health = m_entityManager.m_health[id];
        health.maxHealth = maxHealth;
        health.currentHealth = maxHealth;
        health.regenRate = 1.0f;

        return id;
    }

    void destroyEntity(EntityID id) {
        m_eventSystem.publish("entity:destroyed", &id);
        m_entityManager.destroyEntity(id);
    }

    void run() {
        m_running = true;
        auto lastTime = std::chrono::high_resolution_clock::now();
        float accumulator = 0.0f;
        const float fixedDt = 1.0f / PHYSICS_STEPS_PER_SEC;

        while (m_running) {
            auto now = std::chrono::high_resolution_clock::now();
            float frameTime = std::chrono::duration<float>(now - lastTime).count();
            lastTime = now;

            // ❌ QUALITY: No frame time cap — spiral of death on slow machines
            accumulator += frameTime;

            // Fixed physics steps
            while (accumulator >= fixedDt) {
                m_physicsSystem.step(fixedDt);
                updateScripts(fixedDt);
                accumulator -= fixedDt;
            }

            float interpolation = accumulator / fixedDt;
            m_renderSystem.render(interpolation);

            // Health regen
            updateHealth(fixedDt);

            // Target FPS sleep
            auto elapsed = std::chrono::high_resolution_clock::now() - now;
            auto targetFrame = std::chrono::microseconds(1000000 / m_targetFPS);
            if (elapsed < targetFrame) {
                std::this_thread::sleep_for(targetFrame - elapsed);
            }
        }
    }

    void stop() { m_running = false; }

    void updateScripts(float dt) {
        for (auto& [id, script] : m_entityManager.m_scripts) {
            if (script.enabled && script.onUpdate) {
                // ❌ QUALITY: No exception isolation — one bad script crashes all
                script.onUpdate(id, dt);
            }
        }
    }

    void updateHealth(float dt) {
        for (auto& [id, health] : m_entityManager.m_health) {
            if (health.isAlive() && health.regenRate > 0.0f) {
                health.heal(health.regenRate * dt);
            } else if (!health.isAlive()) {
                m_eventSystem.publish("entity:died", &id);
            }
        }
    }

    void onEntityDied(EntityID id) {
        std::cout << "Entity " << id << " has died.\n";
        // ❌ QUALITY: Destroying entity during iteration — undefined behavior!
        // destroyEntity(id);
    }

    // ─── Save / Load ──────────────────────────────────────────────────────────
    bool saveState(const std::string& filepath) {
        std::ofstream file(filepath);
        if (!file.is_open()) {
            std::cerr << "Cannot open save file: " << filepath << "\n";
            return false;
        }

        file << "SAVE_VERSION=2\n";
        file << "ENTITY_COUNT=" << m_entityManager.entityCount() << "\n";

        for (auto& [id, transform] : m_entityManager.m_transforms) {
            file << "ENTITY " << id << " "
                 << transform.position.x << " "
                 << transform.position.y << " "
                 << transform.position.z << "\n";
        }

        file.close();
        return true;
    }

    // ❌ SECURITY: Loading file path from user input without sanitization
    bool loadState(const std::string& filepath) {
        std::ifstream file(filepath); // Path traversal risk!
        if (!file.is_open()) return false;

        std::string line;
        while (std::getline(file, line)) {
            if (line.substr(0, 7) == "ENTITY ") {
                std::istringstream ss(line.substr(7));
                EntityID id;
                float x, y, z;
                ss >> id >> x >> y >> z;

                if (!m_entityManager.isAlive(id)) {
                    m_entityManager.createEntity(); // ❌ QUALITY: No guarantee correct ID assigned
                }
                m_entityManager.m_transforms[id].position = {x, y, z};
            }
        }
        return true;
    }

    EntityManager m_entityManager;
    ResourceManager m_resourceManager;

private:
    std::atomic<bool> m_running;
    int m_targetFPS;
    PhysicsSystem m_physicsSystem;
    RenderSystem m_renderSystem;
    SceneManager m_sceneManager;
    EventSystem m_eventSystem;
    ThreadPool m_threadPool;
    std::unique_ptr<MemoryPool> m_memoryPool;
};

// ─── Utility Functions ────────────────────────────────────────────────────────
namespace Utils {
    // ❌ SECURITY: Buffer overflow — no bounds check on dest buffer
    void copyString(char* dest, const char* src) {
        strcpy(dest, src); // Should use strncpy or std::string
    }

    // ❌ MEMORY: Allocates but never frees — caller must free, rarely does
    char* formatMessage(const char* fmt, ...) {
        char* buffer = new char[4096];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buffer, 4096, fmt, args);
        va_end(args);
        return buffer; // Caller must delete[] this!
    }

    float lerp(float a, float b, float t) {
        return a + (b - a) * t;
    }

    float clamp(float val, float minVal, float maxVal) {
        return std::max(minVal, std::min(maxVal, val));
    }

    bool fileExists(const std::string& path) {
        std::ifstream f(path);
        return f.good();
    }

    // ❌ DEAD CODE: Never called
    std::vector<std::string> splitString(const std::string& str, char delimiter) {
        std::vector<std::string> tokens;
        std::istringstream ss(str);
        std::string token;
        while (std::getline(ss, token, delimiter)) {
            tokens.push_back(token);
        }
        return tokens;
    }

    // ❌ DEAD CODE
    int _legacy_rand_range(int min, int max) {
        return min + (rand() % (max - min + 1)); // Not thread-safe
    }
}

// ─── Entry Point ──────────────────────────────────────────────────────────────
int main(int argc, char* argv[]) {
    std::cout << "=== CodePulse AI — C++ Engine Sample ===\n\n";

    // ❌ QUALITY: Using argv[1] without checking argc
    std::string sceneName = argc > 1 ? argv[1] : "default";

    GameEngine engine;
    engine.initialize();

    // Load resources
    uint32_t playerTex = engine.m_resourceManager.loadTexture("assets/player.png");
    uint32_t groundTex = engine.m_resourceManager.loadTexture("assets/ground.png");

    // Spawn entities
    EntityID player = engine.spawnCharacter({0.0f, 5.0f, 0.0f}, 100.0f);
    EntityID ground = engine.spawnPhysicsEntity({0.0f, 0.0f, 0.0f});

    auto& groundPhys = engine.m_entityManager.m_physics[ground];
    groundPhys.isStatic = true;

    // Assign render components
    engine.m_entityManager.m_renders[player] = {playerTex, 0, {1.0f, 0.5f, 0.0f}, true, 1};
    engine.m_entityManager.m_renders[ground]  = {groundTex, 0, {0.3f, 0.8f, 0.2f}, true, 0};

    // Script
    engine.m_entityManager.m_scripts[player] = {
        "PlayerController",
        [&](EntityID id, float dt) {
            auto& health = engine.m_entityManager.m_health[id];
            if (!health.isAlive()) return;
        },
        nullptr,
        true
    };

    // ❌ QUALITY: Blocking main thread — should run on separate thread in a real game
    std::cout << "Engine running. Entity count: " << engine.m_entityManager.entityCount() << "\n";

    // Simulate 3 physics steps for demo
    for (int i = 0; i < 3; ++i) {
        engine.m_physicsSystem.step(1.0f / 60.0f);
    }

    engine.saveState("save_game.dat");

    std::cout << "\nSimulation complete. Upload sample_engine.cpp to CodePulse AI for analysis.\n";

    // ❌ MEMORY: engine.m_resourceManager textures never freed — memory leak on exit
    return 0;
}
