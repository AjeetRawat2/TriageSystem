// Store the ID of the currently selected project for the Judge
window.activeProjectId = null;

window.switchToTriage = function() {
    // Reverse the toggle animation back to the cyan Triage state
    document.getElementById('judge-toggle-dot').classList.replace('translate-x-7', 'translate-x-0.5');
    document.getElementById('judge-toggle-bg').classList.replace('bg-fuchsia-900/50', 'bg-cyan-900/50');
    document.getElementById('judge-toggle-bg').classList.replace('border-fuchsia-500/50', 'border-cyan-500/50');
    
    // Wait 300ms for the slide animation to finish before redirecting
    setTimeout(() => {
        window.location.href = window.DJANGO_CONFIG.triageDashboardUrl;
    }, 300);
};

window.showProject = function(id, title, track, abstract, element) {
    window.activeProjectId = id;
    
    // Hide the empty state ring
    document.getElementById('empty-state').classList.add('hidden');
    
    // Show the details panel
    const detailsPanel = document.getElementById('project-details');
    detailsPanel.classList.remove('hidden');
    
    // Trigger CSS reflow to restart fade-in animations
    detailsPanel.style.animation = 'none';
    detailsPanel.offsetHeight; 
    detailsPanel.style.animation = null;
    
    // Inject text data
    document.getElementById('detail-title').textContent = title;
    document.getElementById('detail-track').textContent = track;
    document.getElementById('detail-abstract').textContent = abstract;
    
    // Reset inputs & hide AI area
    document.getElementById('project-score').value = '';
    const aiArea = document.getElementById('ai-response-area');
    if (aiArea) {
        aiArea.classList.add('hidden');
        document.getElementById('ai-summary-text').textContent = '';
    }

    // Highlight the selected card using our hijacked 'ring-2' class
    document.querySelectorAll('.project-card').forEach(card => {
        card.classList.remove('ring-2');
    });
    element.classList.add('ring-2');
};

window.showToast = function(message, type = 'success') {
    const toast = document.createElement('div');
    
    // Cyberpunk themed styles based on success/error
    const borderColor = type === 'success' ? 'border-green-400' : 'border-red-500';
    const textColor = type === 'success' ? 'text-green-400' : 'text-red-400';
    const shadowColor = type === 'success' ? 'shadow-[0_0_15px_rgba(0,255,0,0.3)]' : 'shadow-[0_0_15px_rgba(255,0,0,0.3)]';
    
    toast.className = `fixed top-20 right-8 bg-[#050A15]/95 backdrop-blur-md text-white px-6 py-4 border ${borderColor} ${shadowColor} flex items-center gap-3 fade-in z-50 font-mono-tech uppercase tracking-widest text-[10px]`;
    
    const icon = type === 'success' 
        ? `<svg class="w-5 h-5 ${textColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`
        : `<svg class="w-5 h-5 ${textColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
        
    toast.innerHTML = `${icon} <span>${message}</span>`;
    document.body.appendChild(toast);
    
    // Fade out and remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};

window.submitScore = function() {
    if (!window.activeProjectId) return;
    
    const scoreVal = document.getElementById('project-score').value;
    if (scoreVal === '' || scoreVal < 0 || scoreVal > 100) {
        window.showToast('INVALID_INPUT: SCORE_MUST_BE_0_TO_100', 'error');
        return;
    }

    fetch(`/rate/${window.activeProjectId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.DJANGO_CONFIG.csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ score: scoreVal })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            window.showToast(`SYS_UPDATE: GRADE_${scoreVal}_COMMITTED`, 'success');
            
            // Update the score badge dynamically on the left sidebar
            const activeCard = document.querySelector('.project-card.ring-2');
            if (activeCard) {
                let lvlBadge = activeCard.querySelector('.text-green-400');
                if (lvlBadge) {
                    lvlBadge.textContent = `LVL: ${scoreVal}`;
                } else {
                    const titleArea = activeCard.querySelector('.flex.justify-between.items-center');
                    titleArea.innerHTML += `<span class="text-[10px] font-bold text-green-400 font-mono-tech shadow-[0_0_5px_rgba(0,255,0,0.5)]">LVL: ${scoreVal}</span>`;
                }
            }
        } else {
            window.showToast('ERR: ' + data.message, 'error');
        }
    })
    .catch(err => {
        window.showToast('SYS_FAIL: UPLINK_SEVERED', 'error');
    });
};

window.askJudgeAI = function() {
    if (!window.activeProjectId) return;
    
    const btn = document.getElementById('groq-judge-btn');
    const originalText = btn.innerHTML;
    
    // Tech-style loading state
    btn.innerHTML = `<svg class="animate-spin h-4 w-4 text-fuchsia-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> PROCESSING...`;
    btn.disabled = true;

    fetch(`/judge_summary/${window.activeProjectId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.DJANGO_CONFIG.csrfToken }
    })
    .then(async response => {
        const isJson = response.headers.get('content-type')?.includes('application/json');
        const data = isJson ? await response.json() : null;
        if (!response.ok) throw new Error(data?.message || response.statusText);
        return data;
    })
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if(data.status === 'success') {
            document.getElementById('ai-response-area').classList.remove('hidden');
            document.getElementById('ai-summary-text').textContent = data.summary;
        } else {
            window.showToast("API_ERR: " + data.message, "error");
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        window.showToast("SYS_FAIL: " + err.message, "error");
    });
};