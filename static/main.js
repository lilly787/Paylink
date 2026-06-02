/* main.js - Paylink Core Client SDK */

// Auth System
async function registerUser(fullname, email, phone, password, pin, account_type = 'savings') {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fullname, email, phone, password, pin, account_type })
        });
        const result = await response.json();
        if (result.success) {
            localStorage.setItem('paylink_user', JSON.stringify(result.user));
            return true;
        }
        showToast(result.message || 'Registration failed', 'error');
        return false;
    } catch (e) {
        showToast('Server error', 'error');
        return false;
    }
}

async function loginUser(email, password) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const result = await response.json();
        if (result.success) {
            localStorage.setItem('paylink_user', JSON.stringify(result.user));
            return true;
        }
        showToast(result.message || 'Login failed', 'error');
        return false;
    } catch (e) {
        showToast('Server error', 'error');
        return false;
    }
}

function getUser() {
    const user = localStorage.getItem('paylink_user');
    return user ? JSON.parse(user) : { id: 0, fullname: 'Guest', email: '', balance: 0.00, account_number: '0000000000', is_frozen: 0 };
}

async function refreshUser() {
    const user = getUser();
    if (user.id === 0) return user;
    try {
        const response = await fetch('/api/user/' + user.id);
        if (response.status === 403) {
            // Account is frozen
            logoutUser();
            window.location.href = '/login?msg=frozen';
            return null;
        }
        const result = await response.json();
        if (result.success) {
            localStorage.setItem('paylink_user', JSON.stringify(result.user));
            return result.user;
        }
    } catch(e) {}
    return user;
}

function getInitials(name) {
    if (!name) return 'JD';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function logoutUser() {
    localStorage.removeItem('paylink_user');
}

// Security PIN verification helper
async function verifyPin(pin) {
    const user = getUser();
    try {
        const response = await fetch('/api/verify-pin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id, pin })
        });
        const result = await response.json();
        return result.success;
    } catch(e) {
        return false;
    }
}

// Initialize Toast System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} animate-slide-up`;
    toast.innerHTML = `
        <i data-feather="${type === 'success' ? 'check-circle' : (type === 'warning' ? 'alert-triangle' : 'info')}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    if (window.feather) { feather.replace(); }
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Transactions System using Oracle Database API
async function getTransactions() {
    const user = getUser();
    if (user.id === 0) return [];
    try {
        const response = await fetch('/api/transactions/' + user.id);
        const result = await response.json();
        if (result.success) {
            return result.transactions;
        }
    } catch(e) {}
    return [];
}

async function addTransaction(amount, title, desc, recipientName, recipientAcc, pin, category = 'transfer') {
    const user = getUser();
    if (user.id === 0) return false;
    try {
        const response = await fetch('/api/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: user.id, 
                amount, 
                desc, 
                recipient: recipientName, 
                recipient_acc: recipientAcc, 
                pin,
                category 
            })
        });
        const result = await response.json();
        if (result.success) {
            user.balance = result.balance;
            localStorage.setItem('paylink_user', JSON.stringify(user));
            return result;
        } else {
            showToast(result.message || 'Transaction failed', 'error');
            return null;
        }
    } catch(e) {
        showToast('Server error', 'error');
        return null;
    }
}

function formatCurrency(amount) {
    return '₦' + parseFloat(amount).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatRelDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
        return `Today, ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
    return `${date.toLocaleDateString()}, ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
}

async function fetchOracleRates() {
    try {
        const response = await fetch('/api/oracle/rates');
        const result = await response.json();
        if (result.success && result.oracle) {
            return result.oracle;
        }
    } catch (e) {
        console.error('Oracle fetch failed', e);
    }
    return null;
}

// Feature Not Available yet
window.comingSoon = function(feature) {
    showToast(`${feature} is simulated or coming in the next build!`, 'info');
};

// -- VIRTUAL CARDS SDK --

async function fetchUserCards() {
    const user = getUser();
    try {
        const response = await fetch(`/api/cards/${user.id}`);
        const result = await response.json();
        return result.success ? result.cards : [];
    } catch (e) {
        return [];
    }
}

async function createVirtualCard(amount, pin) {
    const user = getUser();
    try {
        const response = await fetch('/api/cards/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id, amount, pin })
        });
        const result = await response.json();
        if (result.success) {
            showToast('Virtual card created successfully!', 'success');
            return true;
        } else {
            showToast(result.message || 'Failed to create card', 'error');
            return false;
        }
    } catch (e) {
        showToast('Server error', 'error');
        return false;
    }
}

async function toggleCardFreeze(cardId, status) {
    try {
        const response = await fetch('/api/cards/toggle-freeze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_id: cardId, status })
        });
        const result = await response.json();
        if (result.success) {
            showToast(result.message, 'success');
            return true;
        }
        return false;
    } catch (e) {
        showToast('Server error', 'error');
        return false;
    }
}

async function simulateCardTransaction(cardId, amount, merchant) {
    try {
        const response = await fetch('/api/cards/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_id: cardId, amount, merchant })
        });
        const result = await response.json();
        if (result.success) {
            showToast('Card simulated payment successful!', 'success');
            return true;
        } else {
            showToast(result.message || 'Payment declined', 'error');
            return false;
        }
    } catch (e) {
        showToast('Server error', 'error');
        return false;
    }
}

async function fetchCardTransactions(cardId) {
    try {
        const response = await fetch(`/api/cards/transactions/${cardId}`);
        const result = await response.json();
        return result.success ? result.transactions : [];
    } catch (e) {
        return [];
    }
}

// -- BILLS SDK --

async function payBill(amount, billType, provider, meterNumber, pin, phone = '') {
    const user = getUser();
    try {
        const response = await fetch('/api/bills/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.id,
                amount,
                bill_type: billType,
                provider,
                meter_number: meterNumber,
                pin,
                phone
            })
        });
        const result = await response.json();
        if (result.success) {
            user.balance = result.balance;
            localStorage.setItem('paylink_user', JSON.stringify(user));
            return result;
        } else {
            showToast(result.message || 'Bill payment failed', 'error');
            return null;
        }
    } catch (e) {
        showToast('Server error', 'error');
        return null;
    }
}

// -- NOTIFICATIONS SDK --

async function fetchNotifications() {
    const user = getUser();
    try {
        const response = await fetch(`/api/notifications/${user.id}`);
        const result = await response.json();
        return result.success ? result.notifications : [];
    } catch (e) {
        return [];
    }
}

async function markNotificationsAsRead() {
    const user = getUser();
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id })
        });
    } catch (e) {}
}

// Theme toggle logic
function initializeTheme() {
    const savedTheme = localStorage.getItem('paylink_theme');
    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
}
function toggleTheme() {
    if (document.documentElement.getAttribute('data-theme') === 'light') {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('paylink_theme', 'dark');
        return 'dark';
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('paylink_theme', 'light');
        return 'light';
    }
}
// Run immediately
initializeTheme();

// Magnetic footer interaction: items are attracted slightly to the pointer
function initMagneticFooter() {
    const nav = document.querySelector('.bottom-nav');
    if (!nav) return;
    const items = Array.from(nav.querySelectorAll('.nav-item'));
    const maxDist = 140; // px influence radius

    function handleMove(e) {
        const px = e.clientX;
        const py = e.clientY;
        items.forEach(item => {
            const r = item.getBoundingClientRect();
            const cx = r.left + r.width / 2;
            const cy = r.top + r.height / 2;
            const dx = px - cx;
            const dy = py - cy;
            const dist = Math.hypot(dx, dy);
            if (dist < maxDist) {
                const force = (1 - dist / maxDist) * 0.6; // 0..0.6
                const tx = dx * force;
                const ty = dy * force * 0.35; // less vertical movement
                const scale = 1 + 0.06 * force;
                item.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
            } else {
                item.style.transform = '';
            }
        });
    }

    function reset() { items.forEach(i => i.style.transform = ''); }

    // Listen globally so pointer movement still affects the footer while scrolling
    let raf = null;
    function onPointer(e) {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => handleMove(e));
    }

    nav.addEventListener('pointermove', onPointer, { passive: true });
    nav.addEventListener('pointerleave', reset);

    // mobile: only animate when touch is on the nav area, not while scrolling elsewhere
    nav.addEventListener('touchmove', (ev) => {
        if (ev.touches && ev.touches[0]) {
            if (raf) cancelAnimationFrame(raf);
            raf = requestAnimationFrame(() => handleMove(ev.touches[0]));
        }
    }, { passive: true });
    nav.addEventListener('touchend', reset);
}

document.addEventListener('DOMContentLoaded', initMagneticFooter);
