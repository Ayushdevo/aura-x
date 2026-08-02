/**
 * Ayush Tiwari Personal AI Digital Twin & Portfolio App Client
 * Handles data rendering, dynamic themes, particle canvas, chat, and fit analysis.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Generate or fetch session ID for memory storage
    let sessionId = localStorage.getItem("aura_session_id");
    if (!sessionId) {
        sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
        localStorage.setItem("aura_session_id", sessionId);
    }

    // --- Dynamic Theme & Adjustments Configuration ---
    const root = document.documentElement;
    const hueSlider = document.getElementById("hue-slider");
    const hueVal = document.getElementById("hue-val");
    const blurSlider = document.getElementById("blur-slider");
    const blurVal = document.getElementById("blur-val");
    const themePanel = document.getElementById("theme-panel");
    const themePanelBtn = document.getElementById("theme-panel-btn");
    const closeThemeBtn = document.getElementById("close-theme-btn");
    
    // Slide theme control drawer
    themePanelBtn.addEventListener("click", () => themePanel.classList.toggle("open"));
    closeThemeBtn.addEventListener("click", () => themePanel.classList.remove("open"));

    // Hue Control
    hueSlider.addEventListener("input", (e) => {
        const hue = e.target.value;
        hueVal.textContent = `${hue}°`;
        root.style.setProperty("--hue", hue);
        localStorage.setItem("aura_theme_hue", hue);
    });

    // Blur Control
    blurSlider.addEventListener("input", (e) => {
        const blur = e.target.value;
        blurVal.textContent = `${blur}px`;
        root.style.setProperty("--glass-blur", `${blur}px`);
        localStorage.setItem("aura_theme_blur", blur);
    });

    // Restore custom configurations from localStorage
    const savedHue = localStorage.getItem("aura_theme_hue");
    if (savedHue) {
        hueSlider.value = savedHue;
        hueVal.textContent = `${savedHue}°`;
        root.style.setProperty("--hue", savedHue);
    }
    const savedBlur = localStorage.getItem("aura_theme_blur");
    if (savedBlur) {
        blurSlider.value = savedBlur;
        blurVal.textContent = `${savedBlur}px`;
        root.style.setProperty("--glass-blur", `${savedBlur}px`);
    }

    // --- Interactive Background Particle System ---
    const canvas = document.getElementById("bg-canvas");
    const ctx = canvas.getContext("2d");
    let animationId = null;
    let particles = [];
    let isInteractive = true;
    
    const mouse = { x: null, y: null, radius: 120 };
    const spotlight = document.getElementById("cursor-spotlight");
    window.addEventListener("mousemove", (e) => {
        mouse.x = e.x;
        mouse.y = e.y;
        if (spotlight) {
            spotlight.style.left = `${e.clientX}px`;
            spotlight.style.top = `${e.clientY}px`;
            spotlight.style.opacity = 1;
        }
    });
    window.addEventListener("mouseleave", () => {
        mouse.x = null;
        mouse.y = null;
    });

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticles();
    }
    window.addEventListener("resize", resizeCanvas);

    class Particle {
        constructor(x, y, dx, dy, size) {
            this.x = x;
            this.y = y;
            this.dx = dx;
            this.dy = dy;
            this.size = size;
        }
        draw() {
            // Fetch dynamic primary color accent
            const computedStyle = getComputedStyle(root);
            const accentColor = computedStyle.getPropertyValue("--primary").trim();
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = accentColor;
            ctx.shadowBlur = 4;
            ctx.shadowColor = accentColor;
            ctx.fill();
            ctx.shadowBlur = 0; // reset
        }
        update() {
            if (this.x > canvas.width || this.x < 0) this.dx = -this.dx;
            if (this.y > canvas.height || this.y < 0) this.dy = -this.dy;

            // Simple interactive mouse repulsion
            if (isInteractive && mouse.x && mouse.y) {
                let xs = mouse.x - this.x;
                let ys = mouse.y - this.y;
                let distance = Math.sqrt(xs*xs + ys*ys);
                if (distance < mouse.radius) {
                    const force = (mouse.radius - distance) / mouse.radius;
                    this.x -= (xs / distance) * force * 3;
                    this.y -= (ys / distance) * force * 3;
                }
            }

            this.x += this.dx;
            this.y += this.dy;
            this.draw();
        }
    }

    function initParticles() {
        particles = [];
        const quantity = Math.floor((canvas.width * canvas.height) / 11000);
        const limit = Math.min(quantity, 120); // capped for performance
        for (let i = 0; i < limit; i++) {
            let size = Math.random() * 2 + 1;
            let x = Math.random() * canvas.width;
            let y = Math.random() * canvas.height;
            let speedFactor = isInteractive ? 1 : 0.25;
            let dx = (Math.random() - 0.5) * speedFactor;
            let dy = (Math.random() - 0.5) * speedFactor;
            particles.push(new Particle(x, y, dx, dy, size));
        }
    }

    function connectParticles() {
        const computedStyle = getComputedStyle(root);
        const accentHue = computedStyle.getPropertyValue("--hue").trim();
        const maxDist = 120;
        for (let a = 0; a < particles.length; a++) {
            for (let b = a; b < particles.length; b++) {
                let dist = Math.sqrt(
                    (particles[a].x - particles[b].x) ** 2 +
                    (particles[a].y - particles[b].y) ** 2
                );
                if (dist < maxDist) {
                    let alpha = (1 - (dist / maxDist)) * 0.15;
                    ctx.strokeStyle = `hsla(${accentHue}, 90%, 55%, ${alpha})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(particles[a].x, particles[a].y);
                    ctx.lineTo(particles[b].x, particles[b].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
        }
        connectParticles();
        animationId = requestAnimationFrame(animate);
    }

    // Toggle animation speed systems
    document.getElementById("btn-anim-interactive").addEventListener("click", (e) => {
        document.getElementById("btn-anim-slow").classList.remove("active");
        e.target.classList.add("active");
        isInteractive = true;
        initParticles();
    });
    document.getElementById("btn-anim-slow").addEventListener("click", (e) => {
        document.getElementById("btn-anim-interactive").classList.remove("active");
        e.target.classList.add("active");
        isInteractive = false;
        initParticles();
    });

    // Initialize animation canvas
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    initParticles();
    animate();

    // --- Developer Activity Heatmaps Builder ---
    function generateHeatmap(containerId, totalId, activeColorPrefix) {
        const grid = document.getElementById(containerId);
        if (!grid) return;
        grid.innerHTML = "";
        const totalCells = 24 * 7;
        let countSum = 0;
        for (let i = 0; i < totalCells; i++) {
            const cell = document.createElement("div");
            cell.className = "heatmap-cell";
            let weight = Math.random();
            if (Math.random() < 0.25) weight = 0;
            let level = 0;
            let commits = 0;
            if (weight > 0) {
                if (weight < 0.4) { level = 1; commits = Math.floor(Math.random() * 2) + 1; }
                else if (weight < 0.7) { level = 2; commits = Math.floor(Math.random() * 2) + 3; }
                else if (weight < 0.9) { level = 3; commits = Math.floor(Math.random() * 3) + 5; }
                else { level = 4; commits = Math.floor(Math.random() * 4) + 8; }
            }
            countSum += commits;
            if (level > 0) {
                if (activeColorPrefix === "github") {
                    const githubColors = ["rgba(255,255,255,0.03)", "#0e4429", "#006d32", "#26a641", "#39d353"];
                    cell.style.backgroundColor = githubColors[level];
                    cell.style.color = githubColors[level];
                } else {
                    const kaggleColors = ["rgba(255,255,255,0.03)", "#0b4d75", "#0073b1", "#00a2e8", "#00c3ff"];
                    cell.style.backgroundColor = kaggleColors[level];
                    cell.style.color = kaggleColors[level];
                }
            } else {
                cell.style.backgroundColor = "rgba(255, 255, 255, 0.03)";
                cell.style.color = "rgba(255, 255, 255, 0.03)";
            }
            const date = new Date();
            date.setDate(date.getDate() - (totalCells - i));
            const dateStr = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
            const contributionLabel = activeColorPrefix === "github" ? "contributions" : "submissions";
            cell.title = `${commits > 0 ? commits : "No"} ${contributionLabel} on ${dateStr}`;
            grid.appendChild(cell);
        }
        const totalEl = document.getElementById(totalId);
        if (totalEl) {
            totalEl.textContent = `${countSum.toLocaleString()} ${activeColorPrefix === "github" ? "commits" : "kernels"}`;
        }
    }

    generateHeatmap("github-heatmap", "github-total", "github");
    generateHeatmap("kaggle-heatmap", "kaggle-total", "kaggle");

    // --- Portfolio Data Fetching and Displaying ---
    async function loadPortfolioData() {
        try {
            const res = await fetch("/api/resume");
            if (!res.ok) throw new Error("Failed to load resume details");
            const data = await res.json();
            renderResume(data);

            // Fetch active model config dynamically
            const configRes = await fetch("/api/config");
            if (configRes.ok) {
                const configData = await configRes.json();
                const modelEl = document.getElementById("active-model-name");
                if (modelEl) {
                    const modelName = configData.model;
                    // Format output for display (e.g. nemotron-3-ultra-550b-a55b)
                    modelEl.textContent = modelName.split("/").pop().toUpperCase();
                    modelEl.title = modelName;
                }
            }
        } catch (err) {
            console.error("Portfolio retrieval error: ", err);
        }
    }

    function renderResume(data) {
        // Skills Tags
        renderSkillsGroup("skill-languages", data.skills.languages);
        renderSkillsGroup("skill-ml", data.skills.machine_learning_deep_learning);
        renderSkillsGroup("skill-genai", data.skills.generative_ai_llm);
        renderSkillsGroup("skill-data", data.skills.data_engineering);
        renderSkillsGroup("skill-cloud", data.skills.deployment_tools);

        // Experience Timeline
        const expList = document.getElementById("experience-list");
        expList.innerHTML = data.experience.map(exp => `
            <div class="timeline-item">
                <div class="timeline-header">
                    <h4>${exp.company}</h4>
                    <h5>${exp.role}</h5>
                    <span class="date">${exp.duration}</span>
                </div>
                <div class="timeline-body">
                    <p><i class="fa-solid fa-location-dot"></i> ${exp.location}</p>
                    <ul>
                        ${exp.highlights.map(h => `<li>${h}</li>`).join("")}
                    </ul>
                </div>
            </div>
        `).join("");

        // Education Timeline
        const eduList = document.getElementById("education-list");
        eduList.innerHTML = data.education.map(edu => {
            const courseworkHTML = edu.coursework && edu.coursework.length 
                ? `<p class="coursework"><strong>Focus Areas:</strong> ${edu.coursework.join(", ")}</p>` 
                : "";
            return `
                <div class="timeline-item">
                    <div class="timeline-header">
                        <h4>${edu.institution}</h4>
                        <h5>${edu.degree || edu.branch || ''}</h5>
                        <span class="date">${edu.duration}</span>
                    </div>
                    <div class="timeline-body">
                        <p><i class="fa-solid fa-location-dot"></i> ${edu.location}</p>
                        ${courseworkHTML}
                    </div>
                </div>
            `;
        }).join("");

        // Projects Grid
        const projGrid = document.getElementById("projects-list");
        projGrid.innerHTML = data.projects.map(proj => `
            <div class="glass-panel project-card animate-reveal">
                <h4>${proj.name}</h4>
                <div class="badge"><i class="fa-solid fa-calendar-days"></i> ${proj.date}</div>
                <p>${proj.details.join(" ")}</p>
                <div class="skills-tags">
                    ${proj.tech_stack.map(tech => `<span class="skill-tag">${tech}</span>`).join("")}
                </div>
            </div>
        `).join("");

        // Certifications
        const certList = document.getElementById("certifications-list");
        certList.innerHTML = data.certifications.map(cert => `
            <li><i class="fa-solid fa-award"></i> <span>${cert}</span></li>
        `).join("");

        // Achievements
        const achieveList = document.getElementById("achievements-list");
        achieveList.innerHTML = data.key_achievements.map(ach => `
            <li><i class="fa-solid fa-circle-check"></i> <span>${ach}</span></li>
        `).join("");

        // Setup Life Quotes rotation
        const quotes = data.life_quotes || [
            "The best way to predict the future is to invent it.",
            "Data is the new oil, but only if it's refined into intelligence.",
            "Perfection is achieved when there is nothing left to take away."
        ];
        
        const quoteDisplay = document.getElementById("quote-display");
        const nextQuoteBtn = document.getElementById("next-quote-btn");
        let currentQuoteIndex = 0;

        function showQuote(index) {
            if (!quoteDisplay) return;
            quoteDisplay.style.opacity = 0;
            setTimeout(() => {
                quoteDisplay.textContent = `"${quotes[index]}"`;
                quoteDisplay.style.opacity = 1;
            }, 300);
        }

        if (quotes.length > 0) {
            showQuote(0);
        }

        if (nextQuoteBtn) {
            nextQuoteBtn.addEventListener("click", () => {
                currentQuoteIndex = (currentQuoteIndex + 1) % quotes.length;
                showQuote(currentQuoteIndex);
            });
        }

        // Auto rotate quotes every 12 seconds
        setInterval(() => {
            currentQuoteIndex = (currentQuoteIndex + 1) % quotes.length;
            showQuote(currentQuoteIndex);
        }, 12000);
    }

    function renderSkillsGroup(elementId, items) {
        const container = document.getElementById(elementId);
        if (container && items) {
            container.innerHTML = items.map(item => `
                <span class="skill-tag">${item}</span>
            `).join("");
        }
    }

    loadPortfolioData();

    // --- AI Digital Twin Chat Logic ---
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const inspectMemoryBtn = document.getElementById("inspect-memory-btn");
    const closeMemoryBtn = document.getElementById("close-memory-btn");
    const memoryInspector = document.getElementById("memory-inspector");
    const memoryData = document.getElementById("memory-data");

    // Click handler for quick prompts
    document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            chatInput.value = btn.textContent;
            sendMessage();
        });
    });

    // Chat sending triggers
    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    async function sendMessage() {
        const messageText = chatInput.value.trim();
        if (!messageText) return;

        // 1. Render User Message
        appendMessage("user", messageText);
        chatInput.value = "";

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // 2. Render Typing Indicator
        const typingEl = appendTypingIndicator();
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // 3. Post chat payload to backend API
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: messageText
                })
            });

            // Remove typing indicator
            typingEl.remove();

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Server error during chat query");
            }

            const data = await response.json();
            appendMessage("assistant", data.reply);
        } catch (error) {
            typingEl.remove();
            appendMessage("assistant", `Error: ${error.message}. Please verify the API connection or your OpenRouter key limits.`);
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendMessage(role, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${role}-message`);
        messageDiv.innerHTML = `<p>${text.replace(/\n/g, "<br>")}</p>`;
        chatMessages.appendChild(messageDiv);
        return messageDiv;
    }

    function appendTypingIndicator() {
        const indicatorDiv = document.createElement("div");
        indicatorDiv.classList.add("message", "assistant-message", "typing-indicator");
        indicatorDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatMessages.appendChild(indicatorDiv);
        return indicatorDiv;
    }

    // Reset Chat logs
    clearChatBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/reset-session", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId })
            });
            if (res.ok) {
                chatMessages.innerHTML = `
                    <div class="message system-message">
                        <p>Conversation history and twin memory cleared. Ask me anything new!</p>
                    </div>
                `;
            }
        } catch (err) {
            console.error("Failed to reset session: ", err);
        }
    });

    // Inspect Memory Drawer
    inspectMemoryBtn.addEventListener("click", async () => {
        try {
            const res = await fetch(`/api/memory/${sessionId}`);
            if (res.ok) {
                const data = await res.json();
                memoryData.textContent = JSON.stringify(data.logs, null, 2);
                memoryInspector.classList.remove("hidden");
            }
        } catch (err) {
            console.error("Memory retrieval error: ", err);
        }
    });
    closeMemoryBtn.addEventListener("click", () => {
        memoryInspector.classList.add("hidden");
    });


    // --- Compatibility Analyzer System ---
    const jdInput = document.getElementById("jd-input");
    const analyzeBtn = document.getElementById("analyze-btn");
    const analysisResults = document.getElementById("analysis-results");

    analyzeBtn.addEventListener("click", runCompatibilityAnalysis);

    async function runCompatibilityAnalysis() {
        const jd = jdInput.value.trim();
        if (!jd) return;

        // Render Loading State inside results card
        analysisResults.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-spinner fa-spin text-accent"></i>
                <p>Digital Twin analyzing compatibility and skills alignment. Evaluating data store match vectors...</p>
            </div>
        `;

        try {
            const response = await fetch("/api/analyze-compatibility", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_description: jd })
            });

            if (!response.ok) {
                throw new Error("Reasoning engine analysis failed");
            }

            const result = await response.json();
            renderCompatibilityResults(result);

        } catch (err) {
            analysisResults.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-circle-exclamation text-accent"></i>
                    <p>Error running analysis: ${err.message}. Ensure your OpenRouter API has credits and key is active.</p>
                </div>
            `;
        }
    }

    function renderCompatibilityResults(res) {
        // Re-construct the layout template inside the panel
        analysisResults.innerHTML = `
            <div class="results-content">
                <div class="score-row">
                    <div class="circular-progress">
                        <svg viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="40" class="bg-circle"></circle>
                            <circle cx="50" cy="50" r="40" class="fg-circle" id="score-circle"></circle>
                        </svg>
                        <div class="score-number"><span id="score-value">0</span>%</div>
                    </div>
                    <div class="verdict-summary">
                        <h4>Fit Analysis Verdict</h4>
                        <p id="analysis-verdict">${res.fit_verdict}</p>
                    </div>
                </div>
                
                <hr class="divider">
                
                <div class="analysis-details">
                    <div class="detail-col">
                        <h5><i class="fa-solid fa-circle-check text-success"></i> Matching Skills</h5>
                        <div class="skills-tags" id="match-skills-tags">
                            ${res.matching_skills.map(s => `<span class="skill-tag">${s}</span>`).join("")}
                        </div>
                    </div>
                    <div class="detail-col">
                        <h5><i class="fa-solid fa-circle-plus text-accent"></i> Learning Areas</h5>
                        <div class="skills-tags" id="learn-skills-tags">
                            ${res.skills_to_learn.map(s => `<span class="skill-tag">${s}</span>`).join("")}
                        </div>
                    </div>
                </div>
                
                <div class="strengths-gaps">
                    <div class="panel-section">
                        <h5>Core Fit Strengths</h5>
                        <ul id="strengths-list">
                            ${res.strengths.map(st => `<li>${st}</li>`).join("")}
                        </ul>
                    </div>
                    <div class="panel-section">
                        <h5>Honest Gap Analysis</h5>
                        <p id="gaps-text">${res.gaps_analysis}</p>
                    </div>
                </div>
            </div>
        `;

        // Animate the progress stroke offset
        const fgCircle = document.getElementById("score-circle");
        const scoreValue = document.getElementById("score-value");
        const score = res.compatibility_score || 0;
        
        // Circular circumference is 2 * Math.PI * radius = 2 * 3.14159 * 40 = 251.3
        const circumference = 251.2;
        const offset = circumference - (score / 100) * circumference;

        setTimeout(() => {
            fgCircle.style.strokeDashoffset = offset;
            
            // Animate score counter numbers
            let currentScore = 0;
            const timer = setInterval(() => {
                if (currentScore >= score) {
                    clearInterval(timer);
                } else {
                    currentScore++;
                    scoreValue.textContent = currentScore;
                }
            }, 10);
        }, 100);
    }

    // --- Interactive 3D Bot Parallax Tracker ---
    const botContainer = document.getElementById("floating-bot-container");
    const botModel = document.getElementById("bot-3d-model");

    if (botContainer && botModel) {
        // Dynamic clipboard toast alert helper
        function showToast(message) {
            let toast = document.getElementById("bot-toast");
            if (!toast) {
                toast = document.createElement("div");
                toast.id = "bot-toast";
                document.body.appendChild(toast);
            }
            toast.textContent = message;
            toast.classList.add("show");
            setTimeout(() => {
                toast.classList.remove("show");
            }, 3000);
        }

        botContainer.addEventListener("click", () => {
            // Copy to clipboard fallback for 100% click success indication
            navigator.clipboard.writeText("ayushtiwaridsai@gmail.com")
                .then(() => {
                    showToast("Email address copied to clipboard!");
                })
                .catch(() => {
                    showToast("Email: ayushtiwaridsai@gmail.com");
                });

            // Trigger default mailto client
            window.location.href = "mailto:ayushtiwaridsai@gmail.com?subject=Project%20Discussion%20-%20AI%20Portfolio";
        });

        // Current bot position (starts bottom right)
        let botX = window.innerWidth - 120;
        let botY = window.innerHeight - 120;
        let targetX = botX;
        let targetY = botY;
        let isHovered = false;

        botContainer.addEventListener("mouseenter", () => {
            isHovered = true;
            botContainer.classList.add("smile-active");
        });

        botContainer.addEventListener("mouseleave", () => {
            isHovered = false;
            botContainer.classList.remove("smile-active");
        });

        window.addEventListener("mousemove", (e) => {
            const rect = botContainer.getBoundingClientRect();
            const botCenterX = rect.left + rect.width / 2;
            const botCenterY = rect.top + rect.height / 2;

            const dist = Math.hypot(e.clientX - botCenterX, e.clientY - botCenterY);

            // Freeze the bot if hovered OR if the cursor gets closer than 100px (carrot chasing fix)
            if (isHovered || dist < 100) {
                targetX = botX;
                targetY = botY;
                botContainer.classList.add("smile-active");
            } else {
                botContainer.classList.remove("smile-active");
                // Follow cursor with +90px offset (ensures normal distance is 127px, higher than 100px threshold)
                targetX = e.clientX + 90;
                targetY = e.clientY + 90;

                // Keep bot inside screen boundary safely
                const botSize = 100;
                if (targetX > window.innerWidth - botSize) {
                    targetX = e.clientX - botSize - 10;
                }
                if (targetY > window.innerHeight - botSize - 80) {
                    targetY = e.clientY - botSize - 10;
                }
            }
        });

        window.addEventListener("mouseleave", () => {
            // Reset to home base if mouse leaves browser
            targetX = window.innerWidth - 120;
            targetY = window.innerHeight - 120;
            isHovered = false;
            botContainer.classList.remove("smile-active");
        });

        function animateBotFollow() {
            // Smooth lerp (0.07 interpolation rate)
            botX += (targetX - botX) * 0.07;
            botY += (targetY - botY) * 0.07;

            botContainer.style.left = `${botX}px`;
            botContainer.style.top = `${botY}px`;

            // Tilt bot head depending on flight velocity (dx, dy)
            const dx = targetX - botX;
            const dy = targetY - botY;

            const tiltX = Math.min(Math.max(dx * 0.2, -30), 30);
            const tiltY = Math.min(Math.max(dy * 0.2, -30), 30);

            botModel.style.transform = `rotateY(${tiltX}deg) rotateX(${-tiltY}deg)`;

            // Move the eyes slightly for deep cartoon parallax
            const eyes = document.querySelectorAll(".bot-eye");
            const shiftX = Math.min(Math.max(dx * 0.08, -5), 5);
            const shiftY = Math.min(Math.max(dy * 0.08, -3), 3);
            eyes.forEach(eye => {
                eye.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
            });

            requestAnimationFrame(animateBotFollow);
        }

        // Initialize follow animation loop
        requestAnimationFrame(animateBotFollow);
    }
});
