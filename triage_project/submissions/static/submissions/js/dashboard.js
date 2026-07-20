// Store the ID of the currently selected project
window.activeProjectId = null; 

// 1. Initialize Chart.js for the top navigation
document.addEventListener('DOMContentLoaded', function() {
    const rawLabels = window.DJANGO_CONFIG.chartLabels;
    const rawData = window.DJANGO_CONFIG.chartData;
    
    if(rawLabels && rawData && rawLabels !== '""') {
        const labels = JSON.parse(rawLabels);
        const data = JSON.parse(rawData);

        const ctx = document.getElementById('trackChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#0ea5e9'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: context => context.label + ': ' + context.raw } } },
                cutout: '75%'
            }
        });
    }
});

// Switch Mode Animation & Redirect
window.switchToJudge = function() {
    document.getElementById('triage-toggle-dot').classList.replace('translate-x-1', 'translate-x-5');
    document.getElementById('triage-toggle-bg').classList.replace('bg-slate-600', 'bg-indigo-500');
    setTimeout(() => {
        window.location.href = window.DJANGO_CONFIG.judgeDashboardUrl;
    }, 300);
};

// Handle UI interactions for the Triage Inbox
window.showProjectDetails = function(id, title, track, abstract, githubUrl, devpostUrl, element) {
    window.activeProjectId = id;
    
    // Manage Panel Visibility
    document.getElementById('empty-state').classList.add('hidden');
    const detailsPanel = document.getElementById('project-details');
    detailsPanel.classList.remove('hidden');
    
    detailsPanel.style.animation = 'none';
    detailsPanel.offsetHeight; 
    detailsPanel.style.animation = null; 
    
    // Hide the AI Area on new selection
    const aiArea = document.getElementById('ai-response-area');
    if (aiArea) {
        aiArea.classList.add('hidden');
        document.getElementById('ai-summary-text').textContent = '';
    }

    // Populate basic text data
    document.getElementById('detail-title').textContent = title;
    document.getElementById('detail-track').textContent = track;
    document.getElementById('detail-abstract').textContent = abstract;

    // --- DEVPOST PROJECT LINK LOGIC ---
    const devpostLink = document.getElementById('detail-devpost-link');
    const devpostText = document.getElementById('devpost-link-text');
    devpostLink.classList.remove('hidden'); 
    
    if (devpostUrl && devpostUrl.trim() !== "" && devpostUrl !== "None") {
        devpostLink.href = devpostUrl;
        devpostLink.target = "_blank";
        devpostLink.className = "text-[11px] font-mono-tech text-cyan-400 hover:text-white transition-colors flex items-center gap-2 bg-cyan-950/30 border border-cyan-500/30 px-3 py-1.5 shadow-[inset_0_0_10px_rgba(0,255,255,0.1)]";
        if (devpostText) devpostText.textContent = "View original submission";
    } else {
        devpostLink.removeAttribute('href');
        devpostLink.removeAttribute('target');
        devpostLink.className = "text-[11px] font-mono-tech text-slate-500 flex items-center gap-2 bg-slate-900/30 border border-slate-700/50 px-3 py-1.5 cursor-not-allowed";
        if (devpostText) devpostText.textContent = "No Devpost link provided";
    }

    // --- NEW EDITABLE GITHUB LOGIC ---
    const githubSection = document.getElementById('github-section');
    const githubInput = document.getElementById('github-url-input');
    const githubResult = document.getElementById('github-result');
    const validateBtn = document.getElementById('github-validate-btn');
    
    githubSection.classList.remove('hidden'); 
    githubResult.classList.add('hidden');
    githubResult.className = 'hidden mt-1 text-[10px] font-black tracking-wide'; 
    
    // Always enable the button now, since the organizer can type one in!
    validateBtn.innerHTML = '[ EXECUTE_SCAN ]';
    validateBtn.disabled = false;
    validateBtn.classList.remove('opacity-50', 'cursor-not-allowed');

    // Pre-fill if it exists in the database
    if (githubUrl && githubUrl.trim() !== "" && githubUrl !== "None") {
        githubInput.value = githubUrl;
    } else {
        githubInput.value = "";
    }
    
    // UI Selection highlight handling
    document.querySelectorAll('.project-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-indigo-500', 'bg-slate-600', 'border-indigo-500');
    });
    element.classList.add('ring-2', 'ring-indigo-500', 'bg-slate-600', 'border-indigo-500');
};

window.showToast = function(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-emerald-500' : 'bg-slate-700';
    toast.className = `fixed top-20 right-8 ${bgColor} text-white px-6 py-4 rounded-lg shadow-2xl border border-white/10 flex items-center gap-3 fade-in z-50`;
    const icon = type === 'success' 
        ? `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`
        : `<svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
    toast.innerHTML = `${icon} <span class="font-medium">${message}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};

window.approveProject = function() {
    if (!window.activeProjectId) return;
    const track = document.getElementById('detail-track').textContent.trim();
    fetch(`/approve/${window.activeProjectId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.DJANGO_CONFIG.csrfToken, 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            window.showToast(`Success! Project routed to ${track} judging panel.`, 'success');
            const activeCard = document.querySelector('.project-card.ring-2');
            if (activeCard) {
                const statusContainer = activeCard.querySelector('.text-[10px].text-slate-400');
                statusContainer.innerHTML = `<span class="relative inline-flex h-2 w-2 bg-cyan-400 shadow-[0_0_5px_rgba(34,211,238,0.8)]"></span> VRFD`;
            }
        }
    });
};

window.openOverrideModal = function() { document.getElementById('override-modal').classList.remove('hidden'); };
window.closeOverrideModal = function() { document.getElementById('override-modal').classList.add('hidden'); };

window.saveOverride = function() {
    if (!window.activeProjectId) return;
    const newTrack = document.getElementById('new-track-select').value;
    fetch(`/override/${window.activeProjectId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.DJANGO_CONFIG.csrfToken, 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_track: newTrack })
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            window.closeOverrideModal();
            document.getElementById('detail-track').textContent = data.new_track;
            const activeCard = document.querySelector('.project-card.ring-2');
            if (activeCard) {
                const badge = activeCard.querySelector('span.text-indigo-300');
                if (badge) badge.textContent = data.new_track;
            }
            window.showToast(`Project overridden to ${data.new_track}.`, 'success');
        } else { window.showToast('Error: ' + data.message, 'error'); }
    }).catch(err => { window.showToast('Something went wrong!', 'error'); });
};

window.askGroq = function() {
    if (!window.activeProjectId) return;
    const btn = document.getElementById('groq-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Analyzing...`;
    btn.disabled = true;
    fetch(`/summary/${window.activeProjectId}/`, {
        method: 'POST', headers: { 'X-CSRFToken': window.DJANGO_CONFIG.csrfToken }
    })
    .then(async response => {
        const isJson = response.headers.get('content-type')?.includes('application/json');
        const data = isJson ? await response.json() : null;
        if (!response.ok) throw new Error(data?.message || response.statusText);
        return data;
    })
    .then(data => {
        btn.innerHTML = originalText; btn.disabled = false;
        if(data.status === 'success') {
            document.getElementById('ai-response-area').classList.remove('hidden');
            document.getElementById('ai-summary-text').textContent = data.summary;
        } else { window.showToast("Groq API Error: " + data.message, "error"); }
    }).catch(err => {
        btn.innerHTML = originalText; btn.disabled = false;
        window.showToast("Something went wrong! " + err.message, "error");
    });
};

window.validateGithubRepo = function() {
    if (!window.activeProjectId) return;
    
    // Read the new URL from the input box
    const newUrl = document.getElementById('github-url-input').value.trim();
    const btn = document.getElementById('github-validate-btn');
    const resultDiv = document.getElementById('github-result');
    
    if (!newUrl) {
        window.showToast("Please enter a GitHub URL first.", "error");
        return;
    }

    btn.innerHTML = 'ANALYZING...'; 
    btn.disabled = true;
    resultDiv.className = 'hidden mt-1 text-[10px] font-black tracking-wide'; 
    
    // Send the URL in the body of the POST request
    fetch(`/validate-repo/${window.activeProjectId}/`, {
        method: 'POST',
        headers: { 
            'X-CSRFToken': window.DJANGO_CONFIG.csrfToken, 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ github_url: newUrl })
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = '[ EXECUTE_SCAN ]'; 
        btn.disabled = false;
        resultDiv.classList.remove('hidden'); 
        resultDiv.textContent = data.message;
        
        if (data.type === 'fail') { 
            resultDiv.classList.add('text-red-400'); 
        } else if (data.type === 'pass') { 
            resultDiv.classList.add('text-emerald-400'); 
        } else { 
            resultDiv.classList.add('text-amber-400'); 
        }
    }).catch(err => {
        btn.innerHTML = '[ EXECUTE_SCAN ]'; 
        btn.disabled = false;
        window.showToast("GitHub API Error!", "error");
    });
};