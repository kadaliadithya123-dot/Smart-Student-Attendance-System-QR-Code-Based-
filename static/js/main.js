/**
 * Smart Student Attendance System - Vanilla JavaScript Utilities
 * Features: Mobile sidebar, Modal management, Flash alerts, and Pure Canvas Charts
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('mobile-open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('mobile-open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('mobile-open');
      }
    });
  }

  // 2. Auto-dismiss Alert Toasts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(100%)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
});

// Modal Management
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking outside modal box
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});

// Toast notification trigger
function showToast(message, type = 'info') {
  let container = document.querySelector('.alert-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'alert-container';
    document.body.appendChild(container);
  }

  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.innerHTML = `
    <span>${message}</span>
    <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
  `;
  container.appendChild(alert);

  setTimeout(() => {
    alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    setTimeout(() => alert.remove(), 400);
  }, 4500);
}

/* ==========================================================================
   Pure Vanilla Canvas Charts (Zero external libraries)
   ========================================================================== */

const AttendanceCharts = {
  // Bar Chart
  drawBarChart: function(canvasId, labels, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Support High-DPI screens
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 25, right: 20, bottom: 45, left: 45 };

    ctx.clearRect(0, 0, width, height);

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const maxVal = Math.max(...data, 5);
    const barColor = options.color || '#2563eb';
    const numBars = labels.length;
    if (numBars === 0) return;

    const barWidth = Math.min(36, (chartWidth / numBars) * 0.55);
    const barSpacing = chartWidth / numBars;

    // Grid lines & Y-axis labels
    ctx.strokeStyle = '#e2e8f0';
    ctx.fillStyle = '#64748b';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const yVal = Math.round((maxVal / ySteps) * i);
      const yPos = padding.top + chartHeight - (chartHeight / ySteps) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, yPos);
      ctx.lineTo(width - padding.right, yPos);
      ctx.stroke();
      ctx.fillText(yVal + (options.unit || ''), padding.left - 8, yPos);
    }

    // Draw Bars
    labels.forEach((label, idx) => {
      const val = data[idx];
      const barH = (val / maxVal) * chartHeight;
      const x = padding.left + idx * barSpacing + (barSpacing - barWidth) / 2;
      const y = padding.top + chartHeight - barH;

      // Bar rounded top
      ctx.fillStyle = barColor;
      ctx.beginPath();
      const r = Math.min(5, barWidth / 2);
      ctx.moveTo(x, y + barH);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.lineTo(x + barWidth - r, y);
      ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + r);
      ctx.lineTo(x + barWidth, y + barH);
      ctx.closePath();
      ctx.fill();

      // Top value text
      if (val > 0) {
        ctx.fillStyle = '#0f172a';
        ctx.textAlign = 'center';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(val + (options.unit || ''), x + barWidth / 2, y - 8);
      }

      // X-axis label
      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'center';
      ctx.font = '11px sans-serif';
      // Truncate long label if necessary
      const shortLabel = label.length > 14 ? label.substring(0, 12) + '..' : label;
      ctx.fillText(shortLabel, x + barWidth / 2, height - padding.bottom + 18);
    });
  },

  // Line Chart
  drawLineChart: function(canvasId, labels, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 25, right: 20, bottom: 45, left: 45 };

    ctx.clearRect(0, 0, width, height);

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const maxVal = Math.max(...data, 5);
    const lineColor = options.color || '#3b82f6';
    const numPoints = labels.length;
    if (numPoints === 0) return;

    // Y Axis Grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.fillStyle = '#64748b';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const yVal = Math.round((maxVal / ySteps) * i);
      const yPos = padding.top + chartHeight - (chartHeight / ySteps) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, yPos);
      ctx.lineTo(width - padding.right, yPos);
      ctx.stroke();
      ctx.fillText(yVal + (options.unit || ''), padding.left - 8, yPos);
    }

    const points = [];
    const stepX = chartWidth / Math.max(1, numPoints - 1);

    labels.forEach((label, idx) => {
      const val = data[idx];
      const x = padding.left + idx * stepX;
      const y = padding.top + chartHeight - (val / maxVal) * chartHeight;
      points.push({ x, y, val, label });
    });

    // Area fill gradient
    if (points.length > 1) {
      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
      gradient.addColorStop(1, 'rgba(59, 130, 246, 0.01)');

      ctx.beginPath();
      ctx.moveTo(points[0].x, height - padding.bottom);
      ctx.lineTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.lineTo(points[points.length - 1].x, height - padding.bottom);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Line Path
    ctx.beginPath();
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 3;
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();

    // Data dots & X labels
    points.forEach((pt) => {
      // Circle Dot
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = lineColor;
      ctx.stroke();

      // Label below
      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'center';
      ctx.font = '11px sans-serif';
      ctx.fillText(pt.label, pt.x, height - padding.bottom + 18);

      // Value above
      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText(pt.val + (options.unit || ''), pt.x, pt.y - 10);
    });
  }
};
