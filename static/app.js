// static/app.js - HantaMed Assist Production Frontend
// ✅ Cookie + localStorage dual auth, filepath sanitization, legal compliance
// ✅ WCAG 2.1 AA: Focus management, ARIA labels, screen reader support
// ✅ Enhanced UI: Drag-drop visual feedback, loading states, mobile responsive
// ✅ Syntax validated - no unmatched braces/parentheses

(function() {
    'use strict';
    
    const API_BASE = '';
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const form = document.getElementById('analyzeForm');
    const policy = document.getElementById('policyAccept');
    const btn = document.getElementById('submitBtn');
    const progress = document.getElementById('progress');
    const srAnnouncer = document.getElementById('sr-announcer');

    // ✅ WCAG: Announce message to screen readers
    function announce(message) {
        if (srAnnouncer) {
            srAnnouncer.textContent = '';
            setTimeout(function() {
                srAnnouncer.textContent = message;
            }, 100);
        }
    }

    // ✅ Initialize button state on load
    function updateButtonState() {
        if (!btn) return;
        const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
        const policyChecked = policy && policy.checked === true;
        const shouldEnable = hasFile && policyChecked;
        
        btn.disabled = !shouldEnable;
        btn.setAttribute('aria-disabled', String(!shouldEnable));
        
        if (shouldEnable) {
            announce('Form hazır. Analiz Et butonuna basabilirsiniz.');
        }
    }

    // ✅ Enhanced Drag & Drop Handlers with visual feedback
    if (dropZone && fileInput && policy && btn) {
        ['dragenter', 'dragover'].forEach(function(evt) {
            dropZone.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('drag-over');
                dropZone.style.background = '#e0f2fe';
                dropZone.style.borderColor = '#0F4C75';
                announce('Dosyayı bırakmak için sürüklemeye devam edin.');
            });
        });
        
        ['dragleave', 'drop'].forEach(function(evt) {
            dropZone.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');
                dropZone.style.background = '';
                dropZone.style.borderColor = '';
            });
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                var fileName = e.dataTransfer.files[0].name;
                var dropText = dropZone.querySelector('.drop-text');
                if (dropText) dropText.textContent = '✅ ' + fileName;
                announce('Dosya seçildi: ' + fileName);
                updateButtonState();
            }
        });
        
        fileInput.onchange = function() {
            if (fileInput.files && fileInput.files.length > 0) {
                var dropText = dropZone.querySelector('.drop-text');
                if (dropText) dropText.textContent = '✅ ' + fileInput.files[0].name;
                announce('Dosya seçildi: ' + fileInput.files[0].name);
            }
            updateButtonState();
        };
        
        policy.onchange = function() {
            if (policy.checked) {
                announce('Veri işleme politikası onaylandı.');
            }
            updateButtonState();
        };
        
        // ✅ Enhanced Form Submission with loading state
        form.onsubmit = function(e) {
            e.preventDefault();
            
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Lütfen bir dosya seçin.');
                if (fileInput && fileInput.focus) fileInput.focus();
                return;
            }
            if (!policy.checked) {
                alert('Veri işleme politikasını onaylamanız gerekmektedir.');
                if (policy && policy.focus) policy.focus();
                return;
            }
            
            var originalBtnText = btn.innerHTML;
            btn.disabled = true;
            btn.setAttribute('aria-disabled', 'true');
            
            // Show loading state
            var btnText = btn.querySelector('.btn-text');
            var btnLoading = btn.querySelector('.btn-loading');
            if (btnText) btnText.style.display = 'none';
            if (btnLoading) btnLoading.style.display = 'inline';
            
            progress.style.width = '0%';
            progress.setAttribute('aria-valuenow', '0');
            
            announce('Analiz başlatıldı. Lütfen bekleyin.');
            
            var fd = new FormData(form);
            fd.append('accepted_policy', 'true');
            
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/analyze');
            
            var token = localStorage.getItem('token');
            if (token) {
                xhr.setRequestHeader('Authorization', 'Bearer ' + token);
            }
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            
            xhr.upload.onprogress = function(evt) {
                if (evt.lengthComputable) {
                    var percent = Math.min((evt.loaded / evt.total) * 100, 90);
                    progress.style.width = percent + '%';
                    progress.setAttribute('aria-valuenow', String(Math.round(percent)));
                }
            };
            
            xhr.onload = function() {
                progress.style.width = '100%';
                progress.setAttribute('aria-valuenow', '100');
                
                var res;
                try {
                    res = JSON.parse(xhr.responseText);
                } catch (err) {
                    showResult('🔴', 'Hata', 'Sunucu yanıtı okunamadı.', 'Lütfen tekrar deneyin.');
                    announce('Hata: Sunucu yanıtı okunamadı.');
                    resetForm(originalBtnText, btnText, btnLoading);
                    return;
                }
                
                var status = res ? res.status : null;
                var confidence = (res && typeof res.avg_confidence === 'number') ? res.avg_confidence : 0;
                var isFallback = res && res.fallback === true;
                var isRejected = status === 'rejected';
                var isSuccess = status === 'success' && confidence >= 0.7 && !isFallback;
                
                var badge, title, dataText, summary;
                
                if (isRejected) {
                    badge = '🔴';
                    title = 'Belge Reddedildi';
                    dataText = (res && res.reason) ? res.reason : 'Bu belge türü desteklenmemektedir.';
                    summary = (res && res.disclaimer) ? res.disclaimer : 'Yalnızca reçete, laboratuvar raporu veya tahlil görselleri kabul edilmektedir.';
                } else if (isFallback || confidence < 0.7) {
                    badge = '🟡';
                    title = 'Yetersiz Veri / Düşük Güven';
                    
                    var entities = res ? res.entities : null;
                    if (entities && typeof entities === 'object' && Object.keys(entities).length > 0) {
                        var cleanEntities = {};
                        for (var k in entities) {
                            if (entities.hasOwnProperty(k)) {
                                var v = entities[k];
                                if (typeof v === 'object' && v !== null) {
                                    var cleanV = {};
                                    for (var vk in v) {
                                        if (v.hasOwnProperty(vk)) {
                                            var vv = v[vk];
                                            if (typeof vv === 'string' && !vv.match(/[\/\\]|\.(png|jpg|jpeg|gif)$/i)) {
                                                cleanV[vk] = vv;
                                            }
                                        }
                                    }
                                    if (Object.keys(cleanV).length > 0) cleanEntities[k] = cleanV;
                                }
                            }
                        }
                        dataText = Object.keys(cleanEntities).length > 0 
                            ? JSON.stringify(cleanEntities, null, 2)
                            : 'Medikal veri çıkarılamadı.';
                    } else {
                        dataText = 'OCR işlemi tamamlanamadı veya yeterli medikal içerik bulunamadı.';
                    }
                    summary = (res && res.qa_summary) ? res.qa_summary : ((res && res.disclaimer) ? res.disclaimer : 'Lütfen net bir reçete/rapor fotoğrafı yükleyin veya doktorunuza danışın.');
                } else if (isSuccess) {
                    badge = '🟢';
                    title = 'Analiz Tamamlandı';
                    var entities = res ? res.entities : null;
                    if (entities && typeof entities === 'object' && Object.keys(entities).length > 0) {
                        dataText = JSON.stringify(entities, null, 2);
                    } else {
                        dataText = 'Veri çıkarılamadı.';
                    }
                    summary = (res && res.qa_summary) ? res.qa_summary : '';
                } else {
                    badge = '⚪';
                    title = 'Beklenmeyen Durum';
                    dataText = (res && res.message) ? res.message : ((typeof res === 'object' && res !== null) ? JSON.stringify(res, null, 2) : String(res || 'Detay bulunamadı.'));
                    summary = (res && res.disclaimer) ? res.disclaimer : 'Bu sistem yalnızca bilgilendirme amaçlıdır.';
                }
                
                showResult(badge, title, dataText, summary);
                announce(title + '. ' + summary);
                resetForm(originalBtnText, btnText, btnLoading);
            };
            
            xhr.onerror = function() {
                progress.style.width = '100%';
                progress.setAttribute('aria-valuenow', '100');
                showResult('🔴', 'Bağlantı Hatası', 'Sunucuya ulaşılamadı.', 'İnternet bağlantınızı kontrol edin.');
                announce('Hata: Sunucuya ulaşılamadı.');
                resetForm(originalBtnText, btnText, btnLoading);
            };
            
            xhr.send(fd);
        };
    }

    // ✅ Helper: Display result safely with WCAG support
    function showResult(badge, title, dataText, summary) {
        var rc = document.getElementById('resultCard');
        if (!rc) return;
        
        var badgeEl = document.getElementById('badge');
        var titleEl = document.getElementById('resTitle');
        var dataEl = document.getElementById('resData');
        var summaryEl = document.getElementById('resSummary');
        
        if (badgeEl) badgeEl.textContent = badge;
        if (titleEl) titleEl.textContent = title;
        
        if (dataEl) {
            var safeText = (dataText && typeof dataText === 'string' && dataText.trim()) 
                ? dataText.replace(/[A-Za-z]:\\[^\s]+|data\/[^\s]+/g, '[REDACTED]')
                : 'Veri bulunamadı.';
            dataEl.textContent = safeText;
        }
        
        if (summaryEl) {
            summaryEl.textContent = (summary && summary.trim()) ? summary : '';
        }
        
        var disclaimerFooter = document.querySelector('.disclaimer-footer');
        if (disclaimerFooter) {
            disclaimerFooter.textContent = 'Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın.';
        }
        
        rc.classList.remove('hidden');
        if (rc.focus) rc.focus();
        if (rc.scrollIntoView) rc.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ✅ Helper: Reset form state with loading state restoration
    function resetForm(originalHtml, btnText, btnLoading) {
        if (btn) {
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            if (originalHtml) btn.innerHTML = originalHtml;
            if (btnText) btnText.style.display = 'inline';
            if (btnLoading) btnLoading.style.display = 'none';
        }
    }

    // ✅ Admin login with cookie + localStorage dual auth
    var loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.onsubmit = function(e) {
            e.preventDefault();
            var usernameInput = loginForm.querySelector('[name="username"]');
            var passwordInput = loginForm.querySelector('[name="password"]');
            var username = usernameInput ? usernameInput.value.trim() : '';
            var password = passwordInput ? passwordInput.value : '';
            var errorEl = document.getElementById('loginError');
            var submitBtn = loginForm.querySelector('button[type="submit"]');
            
            if (!username || !password) {
                if (errorEl) errorEl.textContent = 'Kullanıcı adı ve şifre gereklidir.';
                if (!username && usernameInput && usernameInput.focus) usernameInput.focus();
                else if (passwordInput && passwordInput.focus) passwordInput.focus();
                return;
            }
            
            if (submitBtn) submitBtn.disabled = true;
            
            var fd = new FormData();
            fd.append('username', username);
            fd.append('password', password);
            
            announce('Giriş yapılıyor...');
            
            fetch('/login', {
                method: 'POST',
                body: fd,
                credentials: 'include'
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.access_token) {
                    localStorage.setItem('token', data.access_token);
                    announce('Giriş başarılı. Yönlendiriliyorsunuz...');
                    window.location.href = '/admin';
                } else {
                    if (errorEl) errorEl.textContent = data.detail || 'Giriş başarısız.';
                    announce('Giriş başarısız: ' + (data.detail || 'Bilinmeyen hata'));
                    if (errorEl && errorEl.focus) errorEl.focus();
                }
            })
            .catch(function(err) {
                console.error('Login error:', err);
                if (errorEl) errorEl.textContent = 'Sunucuya bağlanılamadı.';
                announce('Hata: Sunucuya bağlanılamadı.');
            })
            .finally(function() {
                if (submitBtn) submitBtn.disabled = false;
            });
        };
    }

    // ✅ Admin logout
    var logoutBtn = document.getElementById('logout');
    if (logoutBtn) {
        logoutBtn.onclick = function() {
            announce('Çıkış yapılıyor...');
            localStorage.removeItem('token');
            fetch('/admin/logout', {
                method: 'POST',
                credentials: 'include'
            }).catch(function() {});
            window.location.href = '/login';
        };
    }

    // ✅ Initial button state check on DOM load
    if (typeof document.addEventListener === 'function') {
        document.addEventListener('DOMContentLoaded', function() {
            updateButtonState();
            announce('HantaMed Assist yüklendi. Reçete veya rapor yükleyerek analize başlayabilirsiniz.');
        });
    } else {
        updateButtonState();
    }
    
})();