/**
 * Dr. Shafaei Psychology Clinic - Booking Form Interaction & Client-Side Logic
 * Features: Seamless AJAX, Client-side Image Compression, Accessible Alerts, Dynamic Slots
 */

document.addEventListener("DOMContentLoaded", function () {
    const dateSelect = document.getElementById("date");
    const timeSelect = document.getElementById("time");
    const timeLoading = document.getElementById("timeLoading");
    const receiptInput = document.getElementById("receipt");
    const compressionStatus = document.getElementById("compressionStatus");
    const compressionMsg = document.getElementById("compressionMsg");
    const previewContainer = document.getElementById("previewContainer");
    const receiptPreview = document.getElementById("receiptPreview");
    const bookingForm = document.getElementById("bookingForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const btnSpinner = document.getElementById("btnSpinner");
    const alertContainer = document.getElementById("dynamicAlertContainer");
    const cardBody = document.getElementById("bookingCardBody");
    const copyCardBtn = document.getElementById("copyCardBtn");
    const cardNumberText = document.getElementById("cardNumberText");
    const copyBtnLabel = document.getElementById("copyBtnLabel");

    let compressedReceiptFile = null;

    // کپی آسان شماره کارت با کلیک
    if (copyCardBtn && cardNumberText) {
        copyCardBtn.addEventListener("click", function () {
            const rawText = cardNumberText.innerText.replace(/-/g, "").replace(/\s/g, "");
            navigator.clipboard.writeText(rawText).then(() => {
                copyBtnLabel.textContent = "کپی شد!";
                setTimeout(() => {
                    copyBtnLabel.textContent = "کپی شماره کارت";
                }, 2000);
            }).catch(() => {
                copyBtnLabel.textContent = "کپی ناموفق";
            });
        });
    }

    // تابعی برای ایمن‌سازی متون در برابر XSS
    function escapeHTML(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function showAlert(message, type) {
        if (!alertContainer) return;
        alertContainer.innerHTML = `
            <div class="alert alert-${type === 'danger' ? 'warning' : type} alert-dismissible fade show rounded-3" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i> ${escapeHTML(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="بستن"></button>
            </div>
        `;
        window.scrollTo({ top: alertContainer.offsetTop - 20, behavior: "smooth" });
    }

    function resetSubmitButton() {
        if (!submitBtn) return;
        submitBtn.disabled = false;
        if (btnSpinner) btnSpinner.classList.add("d-none");
        if (btnText) btnText.innerHTML = '<i class="bi bi-check2-circle me-2"></i>ثبت نوبت و ارسال فیش';
    }

    // فشرده‌سازی تصویر در سمت کلاینت با حفظ حداکثر رزولوشن ۱۰۰۰ پیکسل
    function compressImageFile(file) {
        return new Promise((resolve) => {
            if (!file) return resolve(null);
            if (file.size < 120 * 1024 && (file.type === "image/jpeg" || file.type === "image/png")) {
                return resolve(file);
            }

            const objectUrl = URL.createObjectURL(file);
            const img = new Image();

            img.onload = function () {
                URL.revokeObjectURL(objectUrl);
                const maxDim = 1000;
                let w = img.width;
                let h = img.height;

                if (w > maxDim || h > maxDim) {
                    if (w > h) {
                        h = Math.round((h * maxDim) / w);
                        w = maxDim;
                    } else {
                        w = Math.round((w * maxDim) / h);
                        h = maxDim;
                    }
                }

                const canvas = document.createElement("canvas");
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, w, h);

                canvas.toBlob(function (blob) {
                    if (blob) {
                        const optimized = new File([blob], "receipt.jpg", { type: "image/jpeg", lastModified: Date.now() });
                        resolve(optimized);
                    } else {
                        resolve(file);
                    }
                }, "image/jpeg", 0.70);
            };

            img.onerror = function () {
                URL.revokeObjectURL(objectUrl);
                resolve(file);
            };

            img.src = objectUrl;
        });
    }

    // بارگذاری پویای ساعات خالی پس از انتخاب تاریخ
    if (dateSelect && timeSelect) {
        dateSelect.addEventListener("change", function () {
            const selectedDate = this.value;
            if (!selectedDate) return;

            timeSelect.innerHTML = '<option value="" disabled selected>در حال استعلام...</option>';
            if (timeLoading) timeLoading.classList.remove("d-none");

            fetch("/api/available-times/" + encodeURIComponent(selectedDate))
                .then(res => res.json())
                .then(data => {
                    if (timeLoading) timeLoading.classList.add("d-none");
                    timeSelect.innerHTML = "";
                    if (data.available_times && data.available_times.length > 0) {
                        timeSelect.innerHTML = '<option value="" disabled selected>یک ساعت را انتخاب کنید...</option>';
                        data.available_times.forEach(t => {
                            const opt = document.createElement("option");
                            opt.value = t;
                            opt.textContent = t + " تا " + (parseInt(t.split(":")[0]) + 1) + ":00";
                            timeSelect.appendChild(opt);
                        });
                    } else {
                        timeSelect.innerHTML = '<option value="" disabled selected>ظرفیت نوبت‌های این تاریخ تکمیل است</option>';
                    }
                })
                .catch(() => {
                    if (timeLoading) timeLoading.classList.add("d-none");
                    timeSelect.innerHTML = '<option value="" disabled selected>خطا در دریافت ساعات. مجدداً انتخاب کنید.</option>';
                });
        });
    }

    // آماده‌سازی و پیش‌نمایش تصویر رسید
    if (receiptInput) {
        receiptInput.addEventListener("change", async function () {
            const file = this.files && this.files[0];
            if (!file) {
                compressedReceiptFile = null;
                if (previewContainer) previewContainer.classList.add("d-none");
                if (compressionStatus) compressionStatus.classList.add("d-none");
                return;
            }

            if (compressionMsg) compressionMsg.textContent = "در حال آماده‌سازی تصویر...";
            if (compressionStatus) compressionStatus.classList.remove("d-none");

            compressedReceiptFile = await compressImageFile(file);

            if (compressedReceiptFile) {
                const kb = Math.round(compressedReceiptFile.size / 1024);
                const previewUrl = URL.createObjectURL(compressedReceiptFile);
                if (receiptPreview) receiptPreview.src = previewUrl;
                if (previewContainer) previewContainer.classList.remove("d-none");
                if (compressionMsg) compressionMsg.textContent = "تصویر فیش آماده شد (" + kb + " کیلوبایت)";
            }
        });
    }

    // ثبت فرم به شیوه ایجکس
    if (bookingForm) {
        bookingForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const fullName = document.getElementById("full_name").value.trim();
            const phone = document.getElementById("phone").value.trim();
            const sessionType = document.getElementById("session_type").value;
            const date = document.getElementById("date").value;
            const time = document.getElementById("time").value;

            if (!fullName || !phone || !sessionType || !date || !time) {
                showAlert("لطفاً تمام فیلدهای مشخصات، تاریخ و ساعت را انتخاب فرمایید.", "danger");
                return;
            }

            const rawFile = receiptInput && receiptInput.files && receiptInput.files[0];
            if (!rawFile && !compressedReceiptFile) {
                showAlert("لطفاً تصویر فیش پرداخت را انتخاب فرمایید.", "danger");
                return;
            }

            if (submitBtn) submitBtn.disabled = true;
            if (btnSpinner) btnSpinner.classList.remove("d-none");
            if (btnText) btnText.textContent = "در حال ارسال و ثبت نوبت...";

            // اطمینان از پایان فشرده‌سازی
            let fileToSend = compressedReceiptFile;
            if (!fileToSend && rawFile) {
                if (btnText) btnText.textContent = "در حال بهینه‌سازی فیش...";
                fileToSend = await compressImageFile(rawFile);
                if (btnText) btnText.textContent = "در حال ارسال و ثبت نوبت...";
            }

            const formData = new FormData();
            const csrfTokenEl = document.querySelector('input[name="csrf_token"]');
            if (csrfTokenEl) {
                formData.append("csrf_token", csrfTokenEl.value);
            }
            formData.append("is_ajax", "1");
            formData.append("full_name", fullName);
            formData.append("phone", phone);
            formData.append("session_type", sessionType);
            formData.append("date", date);
            formData.append("time", time);
            formData.append("receipt", fileToSend || rawFile, "receipt.jpg");

            try {
                const res = await fetch("/booking", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                });

                const data = await res.json().catch(() => null);

                if (res.ok && data && data.success) {
                    const safeName = escapeHTML(data.full_name || fullName);
                    const safeDate = escapeHTML(data.date);
                    const safeTime = escapeHTML(data.time);
                    const safeType = escapeHTML(data.session_type || sessionType);
                    const safeId = escapeHTML(data.appointment_id);

                    if (cardBody) {
                        cardBody.innerHTML = `
                            <div class="text-center py-4">
                                <div class="mb-3">
                                    <span class="d-inline-flex align-items-center justify-content-center rounded-circle" style="width: 80px; height: 80px; background-color: var(--light-green); color: var(--primary-green); font-size: 2.8rem;">
                                        <i class="bi bi-check2"></i>
                                    </span>
                                </div>
                                <h3 class="fw-bold mb-3" style="color: var(--primary-green);">درخواست نوبت شما با موفقیت ثبت شد</h3>
                                <p class="text-muted fs-5 mb-4">کد پیگیری نوبت: <span class="badge bg-light text-dark border fs-5 font-monospace">#${safeId}</span></p>
                                
                                <div class="p-4 rounded-4 bg-light text-dark mb-4 text-start mx-auto" style="max-width: 480px; border: 1px solid var(--subtle-border);">
                                    <div class="d-flex justify-content-between border-bottom py-2">
                                        <span class="text-muted">مراجع محترم:</span>
                                        <span class="fw-bold">${safeName}</span>
                                    </div>
                                    <div class="d-flex justify-content-between border-bottom py-2">
                                        <span class="text-muted">تاریخ جلسه:</span>
                                        <span class="fw-bold">${safeDate}</span>
                                    </div>
                                    <div class="d-flex justify-content-between border-bottom py-2">
                                        <span class="text-muted">ساعت جلسه:</span>
                                        <span class="fw-bold">${safeTime}</span>
                                    </div>
                                    <div class="d-flex justify-content-between py-2">
                                        <span class="text-muted">نوع جلسه:</span>
                                        <span class="fw-bold">${safeType}</span>
                                    </div>
                                </div>

                                <div class="alert alert-light border small mx-auto text-muted lh-lg" style="max-width: 520px; background-color: var(--cream-bg);">
                                    <i class="bi bi-info-circle me-1" style="color: var(--primary-green);"></i>
                                    رسید پرداخت شما برای واحد پذیرش کلینیک ارسال گردید. پس از بازبینی فیش توسط منشی، جهت هماهنگی نهایی با شماره تماس شما ارتباط برقرار خواهد شد.
                                </div>

                                <div class="d-flex justify-content-center gap-3 mt-4">
                                    <a href="/" class="btn btn-primary rounded-pill px-4">صفحه اصلی کلینیک</a>
                                    <a href="/booking" class="btn btn-outline-primary rounded-pill px-4">ثبت نوبت دیگر</a>
                                </div>
                            </div>
                        `;
                    }
                    window.scrollTo({ top: 0, behavior: "smooth" });
                } else {
                    const errorMsg = (data && data.error) ? data.error : "متاسفانه در ثبت نوبت خطایی رخ داد. لطفاً مجدداً تلاش فرمایید.";
                    showAlert(errorMsg, "danger");
                    resetSubmitButton();
                }
            } catch (fetchErr) {
                console.error("Booking submission network error:", fetchErr);
                showAlert("خطا در برقراری ارتباط با سرور (" + (fetchErr.message || "Network Error") + "). لطفاً وضعیت اینترنت را بررسی فرمایید.", "danger");
                resetSubmitButton();
            }
        });
    }
});
