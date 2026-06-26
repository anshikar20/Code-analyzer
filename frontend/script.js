let debounceTimer;

// Backend endpoints
const QUICK_SCAN_URL = "http://127.0.0.1:8000/analyze/quick";
const FULL_SCAN_URL = "http://127.0.0.1:8000/analyze/full";
const CUSTOM_RULES_URL = "http://127.0.0.1:8000/custom-rules";
const DEPENDENCY_SCAN_URL = "http://127.0.0.1:8000/analyze/dependencies";


// Common function used for both quick and full scan
async function analyzeCode(endpoint, modeName) {
    const code = document.getElementById("codeInput").value;
    const language = document.getElementById("languageSelect").value;

    const customRulesToggle = document.getElementById("customRulesToggle");
    const enableCustomRules = customRulesToggle ? customRulesToggle.checked : false;

    const summaryBox = document.getElementById("summaryBox");
    const resultBox = document.getElementById("resultBox");
    const modeText = document.getElementById("modeText");

    if (!code.trim()) {
        modeText.innerText = "Mode: Waiting";
        summaryBox.innerHTML = "<h2>Summary</h2><p>No code entered.</p>";
        resultBox.innerHTML = "<h2>Issues</h2><p>Please write some code first.</p>";
        return;
    }

    modeText.innerText = `Mode: ${modeName} running...`;
    summaryBox.innerHTML = "<h2>Summary</h2><p>Analyzing...</p>";
    resultBox.innerHTML = "<h2>Issues</h2><p>Please wait...</p>";

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                language: language,
                code: code,
                enable_custom_rules: enableCustomRules
            })
        });

        const data = await response.json();

        modeText.innerText = `Mode: ${data.mode || modeName} completed`;

        displaySummary(data.summary);
        displayIssues(data.issues);

    } catch (error) {
        modeText.innerText = "Mode: Failed";
        summaryBox.innerHTML = "<h2>Summary</h2><p>Request failed.</p>";
        resultBox.innerHTML = `<h2>Issues</h2><p>${error}</p>`;
    }
}


// Full scan runs when button is clicked
async function analyzeFullCode() {
    await analyzeCode(FULL_SCAN_URL, "Full Scan");
}


// Quick scan runs automatically while typing
async function analyzeQuickCode() {
    await analyzeCode(QUICK_SCAN_URL, "Quick Scan");
}


// Save custom rule
async function saveCustomRule() {
    const name = document.getElementById("ruleName").value.trim();
    const language = document.getElementById("ruleLanguage").value;
    const type = document.getElementById("ruleType").value;
    const severity = document.getElementById("ruleSeverity").value;
    const pattern = document.getElementById("rulePattern").value.trim();
    const message = document.getElementById("ruleMessage").value.trim();
    const enabled = document.getElementById("ruleEnabled").checked;

    if (!name || !pattern || !message) {
        alert("Please fill rule name, pattern, and message.");
        return;
    }

    try {
        const response = await fetch(CUSTOM_RULES_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                language: language,
                type: type,
                pattern: pattern,
                severity: severity,
                message: message,
                enabled: enabled
            })
        });

        const data = await response.json();

        if (data.status === "completed") {
            alert("Custom rule saved successfully.");
            clearCustomRuleForm();
            loadCustomRules();
        } else {
            alert(data.message || "Failed to save custom rule.");
        }

    } catch (error) {
        alert("Error saving custom rule: " + error);
    }
}


// Load custom rules
async function loadCustomRules() {
    const customRulesList = document.getElementById("customRulesList");

    if (!customRulesList) {
        return;
    }

    customRulesList.innerHTML = "<p>Loading custom rules...</p>";

    try {
        const response = await fetch(CUSTOM_RULES_URL);
        const data = await response.json();

        if (!data.rules || data.rules.length === 0) {
            customRulesList.innerHTML = "<p>No custom rules found.</p>";
            return;
        }

        let html = "<h3>Existing Custom Rules</h3>";

        data.rules.forEach((rule, index) => {
            html += `
                <div class="custom-rule-card">
                    <div><strong>${index + 1}. ${escapeHtml(rule.name)}</strong></div>
                    <div><strong>Language:</strong> ${escapeHtml(rule.language)}</div>
                    <div><strong>Type:</strong> ${escapeHtml(rule.type)}</div>
                    <div><strong>Pattern:</strong> <code>${escapeHtml(rule.pattern)}</code></div>
                    <div><strong>Severity:</strong> ${escapeHtml(rule.severity)}</div>
                    <div><strong>Enabled:</strong> ${rule.enabled}</div>
                    <div>
                            <strong>Status:</strong>
                            <span class="${rule.enabled ? "rule-enabled" : "rule-disabled"}">
                             ${rule.enabled ? "Enabled" : "Disabled"}
                     </span>
                    </div>

                     <div class="rule-message">${escapeHtml(rule.message)}</div>

                    <div class="rule-actions">
                      <button class="toggle-rule-btn" onclick="toggleCustomRule(${index})">
                            ${rule.enabled ? "Disable Rule" : "Enable Rule"}
                        </button>

                        <button class="delete-rule-btn" onclick="deleteCustomRule(${index})">
                        Delete Rule
                         </button>
                 </div>
                
            `;
        });

        customRulesList.innerHTML = html;

    } catch (error) {
        customRulesList.innerHTML = `<p>Failed to load custom rules: ${error}</p>`;
    }
}

//depemdency function
async function checkDependencies() {
    const dependencyResultBox = document.getElementById("dependencyResultBox");

    dependencyResultBox.innerHTML = "<p>Checking dependencies...</p>";

    try {
        const response = await fetch(DEPENDENCY_SCAN_URL);
        const data = await response.json();

        if (!data.issues || data.issues.length === 0) {
            dependencyResultBox.innerHTML = `
                <div class="dependency-success">
                    ✅ No dependency issues found.
                </div>
            `;
            return;
        }

        let html = "<h3>Dependency Scan Results</h3>";

        data.issues.forEach(issue => {
            html += `
                <div class="dependency-card ${issue.severity}">
                    <div><strong>Tool:</strong> ${escapeHtml(issue.tool || "pip-audit")}</div>
                    <div><strong>Type:</strong> ${escapeHtml(issue.type || "dependency")}</div>
                    <div><strong>Severity:</strong> ${escapeHtml(issue.severity || "warning")}</div>
                    <div class="message">${escapeHtml(issue.message || "")}</div>
                </div>
            `;
        });

        dependencyResultBox.innerHTML = html;

    } catch (error) {
        dependencyResultBox.innerHTML = `
            <div class="dependency-card error">
                <strong>Dependency scan failed:</strong> ${escapeHtml(error.message)}
            </div>
        `;
    }
}



//enable toggle

async function toggleCustomRule(index) {
    try {
        const response = await fetch(`${CUSTOM_RULES_URL}/${index}/toggle`, {
            method: "PATCH"
        });

        const data = await response.json();

        if (data.status === "completed") {
            loadCustomRules();
        } else {
            alert(data.message || "Failed to update custom rule status.");
        }

    } catch (error) {
        alert("Error updating custom rule: " + error);
    }
}

//delete custom rules
async function deleteCustomRule(index) {
    const confirmDelete = confirm("Are you sure you want to delete this custom rule?");

    if (!confirmDelete) {
        return;
    }

    try {
        const response = await fetch(`${CUSTOM_RULES_URL}/${index}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (data.status === "completed") {
            alert("Custom rule deleted successfully.");
            loadCustomRules();
        } else {
            alert(data.message || "Failed to delete custom rule.");
        }

    } catch (error) {
        alert("Error deleting custom rule: " + error);
    }
}


// Helper function to clear custom rule form
function clearCustomRuleForm() {
    document.getElementById("ruleName").value = "";
    document.getElementById("rulePattern").value = "";
    document.getElementById("ruleMessage").value = "";
    document.getElementById("ruleLanguage").value = "any";
    document.getElementById("ruleType").value = "contains";
    document.getElementById("ruleSeverity").value = "warning";
    document.getElementById("ruleEnabled").checked = true;
}


// Escape HTML to safely display user-entered rule values
function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// Display summary result
function displaySummary(summary) {
    const summaryBox = document.getElementById("summaryBox");

    if (!summary) {
        summaryBox.innerHTML = "<h2>Summary</h2><p>No summary available.</p>";
        return;
    }

    summaryBox.innerHTML = `
        <h2>Summary</h2>
        <p><strong>Total Issues:</strong> ${summary.total}</p>
        <p><strong>Errors:</strong> ${summary.errors}</p>
        <p><strong>Warnings:</strong> ${summary.warnings}</p>
        <p><strong>Info:</strong> ${summary.info}</p>
    `;
}


// Display issue cards
function displayIssues(issues) {
    const resultBox = document.getElementById("resultBox");

    if (!issues || issues.length === 0) {
        resultBox.innerHTML = `
            <h2>Issues</h2>
            <p>No issues found ✅</p>
        `;
        return;
    }

    let html = "<h2>Issues</h2>";

    issues.forEach(issue => {
        html += `
            <div class="issue-card ${issue.severity}">
                <div><strong>Tool:</strong> ${escapeHtml(issue.tool || "unknown")}</div>
                <div><strong>Type:</strong> ${escapeHtml(issue.type || "unknown")}</div>
                <div><strong>Severity:</strong> ${escapeHtml(issue.severity || "info")}</div>
                ${issue.line ? `<div><strong>Line:</strong> ${issue.line}</div>` : ""}
                <div class="message">${escapeHtml(issue.message || "")}</div>
            </div>
        `;
    });

    resultBox.innerHTML = html;
}

//dark mode function
function toggleTheme() {
    document.body.classList.toggle("dark-mode");

    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");

    updateThemeButton();
}


function updateThemeButton() {
    const themeToggleBtn = document.getElementById("themeToggleBtn");

    if (!themeToggleBtn) {
        return;
    }

    if (document.body.classList.contains("dark-mode")) {
        themeToggleBtn.innerText = "☀️ Light Mode";
    } else {
        themeToggleBtn.innerText = "🌙 Dark Mode";
    }
}


function loadSavedTheme() {
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    updateThemeButton();
}

// Debounce logic for real-time quick scan
document.getElementById("codeInput").addEventListener("input", function () {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
        analyzeQuickCode();
    }, 2000);
});


// Run quick scan when language changes
document.getElementById("languageSelect").addEventListener("change", function () {
    analyzeQuickCode();
});


// Load rules automatically when frontend opens
window.addEventListener("load", function () {
    loadCustomRules();
    loadSavedTheme();
});

