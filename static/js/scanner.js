/**
 * Smart Student Attendance System - QR Scanner Controller
 * Uses bundled html5-qrcode.min.js with Web Audio API sound synthesis.
 */

let html5QrCode = null;
let isScanning = false;
let lastScannedCode = null;
let lastScannedTime = 0;
const SCAN_COOLDOWN_MS = 3000; // 3-second throttle for the same code

// Web Audio API Synth for instant audio feedback without external audio assets
const AudioFeedback = {
  ctx: null,

  init: function() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  },

  playSuccess: function() {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, this.ctx.currentTime); // A5
      osc.frequency.exponentialRampToValueAtTime(1320, this.ctx.currentTime + 0.15); // E6
      gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.25);
    } catch (e) {
      console.warn("Audio error", e);
    }
  },

  playWarning: function() {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(360, this.ctx.currentTime);
      osc.frequency.setValueAtTime(280, this.ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.28);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.28);
    } catch (e) {
      console.warn("Audio error", e);
    }
  },

  playError: function() {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.3);
    } catch (e) {
      console.warn("Audio error", e);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('startScanBtn');
  const stopBtn = document.getElementById('stopScanBtn');
  const cameraSelect = document.getElementById('cameraSelect');
  const manualForm = document.getElementById('manualSubmitForm');

  html5QrCode = new Html5Qrcode("reader");

  // Populate cameras
  Html5Qrcode.getCameras().then(cameras => {
    if (cameras && cameras.length) {
      cameraSelect.innerHTML = '';
      cameras.forEach((camera, index) => {
        const option = document.createElement('option');
        option.value = camera.id;
        option.text = camera.label || `Camera ${index + 1}`;
        cameraSelect.appendChild(option);
      });
      cameraSelect.disabled = false;
    } else {
      cameraSelect.innerHTML = '<option value="">No cameras found</option>';
    }
  }).catch(err => {
    console.warn("Camera enum error:", err);
    cameraSelect.innerHTML = '<option value="">Camera access unavailable</option>';
  });

  if (startBtn) startBtn.addEventListener('click', startScanner);
  if (stopBtn) stopBtn.addEventListener('click', stopScanner);

  if (manualForm) {
    manualForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('manualStudentId');
      if (input && input.value.trim()) {
        processStudentCode(input.value.trim().toUpperCase());
        input.value = '';
      }
    });
  }
});

function startScanner() {
  const cameraSelect = document.getElementById('cameraSelect');
  const cameraId = cameraSelect ? cameraSelect.value : null;
  const startBtn = document.getElementById('startScanBtn');
  const stopBtn = document.getElementById('stopScanBtn');

  const config = {
    fps: 10,
    qrbox: { width: 250, height: 250 },
    aspectRatio: 1.0
  };

  const cameraConfig = cameraId ? { deviceId: { exact: cameraId } } : { facingMode: "environment" };

  html5QrCode.start(
    cameraConfig,
    config,
    (decodedText) => {
      const now = Date.now();
      if (decodedText === lastScannedCode && (now - lastScannedTime) < SCAN_COOLDOWN_MS) {
        return; // throttled
      }
      lastScannedCode = decodedText;
      lastScannedTime = now;
      processStudentCode(decodedText.trim().toUpperCase());
    },
    (errorMessage) => {
      // scanning frame didn't find qr; non-critical
    }
  ).then(() => {
    isScanning = true;
    if (startBtn) startBtn.style.display = 'none';
    if (stopBtn) stopBtn.style.display = 'inline-flex';
    setFeedback("Camera active. Point at Student QR code...", "info");
  }).catch(err => {
    console.error("Failed to start scanner:", err);
    setFeedback("Could not start camera. Please verify permissions or use manual ID entry below.", "error");
  });
}

function stopScanner() {
  if (html5QrCode && isScanning) {
    html5QrCode.stop().then(() => {
      isScanning = false;
      const startBtn = document.getElementById('startScanBtn');
      const stopBtn = document.getElementById('stopScanBtn');
      if (startBtn) startBtn.style.display = 'inline-flex';
      if (stopBtn) stopBtn.style.display = 'none';
      setFeedback("Scanner paused.", "info");
    }).catch(err => console.error("Error stopping scanner", err));
  }
}

function setFeedback(msg, type) {
  const badge = document.getElementById('scannerFeedback');
  if (!badge) return;
  badge.className = `scan-feedback-badge ${type}`;
  badge.textContent = msg;
  badge.style.display = 'block';
}

function processStudentCode(studentId) {
  setFeedback(`Verifying Student ID: ${studentId}...`, "info");

  fetch('/faculty/mark_attendance', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ student_id: studentId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      AudioFeedback.playSuccess();
      setFeedback(`✓ ${data.message}: ${data.student.name} (${data.student.student_id})`, 'success');
      appendScanLog(data.student, 'Present', 'badge-success');
    } else if (data.already_marked) {
      AudioFeedback.playWarning();
      setFeedback(`⚠ ${data.message}: ${data.student ? data.student.name : studentId}`, 'warning');
      appendScanLog({ student_id: studentId, name: data.student?.name || 'Student', department: data.student?.department || '-' }, 'Already Marked', 'badge-warning');
    } else {
      AudioFeedback.playError();
      setFeedback(`✗ ${data.message}`, 'error');
    }
  })
  .catch(err => {
    AudioFeedback.playError();
    setFeedback(`Network error contacting server`, 'error');
  });
}

function appendScanLog(student, statusText, badgeClass) {
  const tbody = document.getElementById('liveScanLogBody');
  if (!tbody) return;

  const noRow = document.getElementById('noLiveScansRow');
  if (noRow) noRow.remove();

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><strong>${student.student_id}</strong></td>
    <td>${student.name}</td>
    <td>${student.department || '-'}</td>
    <td>${timeStr}</td>
    <td><span class="badge ${badgeClass}">${statusText}</span></td>
  `;
  tbody.insertBefore(tr, tbody.firstChild);
}
