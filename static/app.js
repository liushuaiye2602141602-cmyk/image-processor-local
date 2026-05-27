/**
 * app.js - 图片处理工具前端逻辑
 */

(function () {
    'use strict';

    // DOM 元素
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const fileNameList = document.getElementById('fileNameList');
    const fileCount = document.getElementById('fileCount');
    const btnClear = document.getElementById('btnClear');
    const instruction = document.getElementById('instruction');
    const btnProcess = document.getElementById('btnProcess');
    const processing = document.getElementById('processing');
    const errorBox = document.getElementById('errorBox');
    const resultSingle = document.getElementById('resultSingle');
    const resultBatch = document.getElementById('resultBatch');
    const qualitySection = document.getElementById('qualitySection');
    const qualitySlider = document.getElementById('qualitySlider');
    const qualityInput = document.getElementById('qualityInput');
    const compressDesc = document.getElementById('compressDesc');
    const qualityHint = document.getElementById('qualityHint');

    let selectedFiles = [];

    // 压缩模式描述
    var modeDescs = {
        none: '不压缩，只做格式转换，quality = 100',
        recommended: '适合网站图片优化，清晰度优先（quality = 90）',
        custom: '拖动滑块或输入数值自定义压缩比例（60-100）'
    };

    // 压缩模式切换
    document.querySelectorAll('input[name="compressMode"]').forEach(function (radio) {
        radio.addEventListener('change', function () {
            compressDesc.textContent = modeDescs[radio.value] || '';
            if (radio.value === 'custom') {
                qualitySection.style.display = 'block';
            } else {
                qualitySection.style.display = 'none';
            }
        });
    });

    // 滑块与输入框联动
    if (qualitySlider && qualityInput) {
        qualitySlider.addEventListener('input', function () {
            qualityInput.value = qualitySlider.value;
            validateQuality(qualitySlider.value);
        });
        qualityInput.addEventListener('input', function () {
            var val = parseInt(qualityInput.value, 10);
            if (isNaN(val)) return;
            val = Math.max(60, Math.min(100, val));
            qualitySlider.value = val;
            validateQuality(val);
        });
        qualityInput.addEventListener('blur', function () {
            var val = parseInt(qualityInput.value, 10);
            if (isNaN(val) || val < 60) {
                qualityInput.value = 90;
                qualitySlider.value = 90;
                validateQuality(90);
            } else if (val > 100) {
                qualityInput.value = 100;
                qualitySlider.value = 100;
                validateQuality(100);
            }
        });
    }

    // 质量验证提示
    function validateQuality(val) {
        if (val < 60) {
            qualityHint.textContent = '⚠️ 低于 60 可能导致图片明显模糊！';
            qualityHint.style.color = '#e53e3e';
        } else if (val < 72) {
            qualityHint.textContent = '⚠️ 较低质量，画质损失较明显';
            qualityHint.style.color = '#dd6b20';
        } else {
            qualityHint.textContent = '推荐 90，低于 60 可能导致图片明显模糊';
            qualityHint.style.color = '#888';
        }
    }

    // 获取当前压缩模式和参数
    function getCompressMode() {
        var checked = document.querySelector('input[name="compressMode"]:checked');
        return checked ? checked.value : 'recommended';
    }

    // 获取最终发送给后端的 compress_mode 和 quality
    function getCompressParams() {
        var mode = getCompressMode();
        if (mode === 'none') {
            return { compress_mode: 'none' };
        }
        if (mode === 'recommended') {
            return { compress_mode: 'lossy', quality: 90 };
        }
        // custom
        var q = parseInt(qualityInput.value, 10);
        if (isNaN(q) || q < 60) q = 90;
        if (q > 100) q = 100;
        return { compress_mode: 'lossy', quality: q };
    }

    // 上传区域点击
    uploadArea.addEventListener('click', function () {
        fileInput.click();
    });

    // 拖拽
    uploadArea.addEventListener('dragover', function (e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function () {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function (e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    // 文件选择
    fileInput.addEventListener('change', function () {
        handleFiles(fileInput.files);
    });

    // 处理选择的文件
    function handleFiles(files) {
        selectedFiles = Array.from(files);
        updateFileList();
    }

    // 更新文件列表显示
    function updateFileList() {
        if (selectedFiles.length === 0) {
            fileList.style.display = 'none';
            return;
        }

        fileList.style.display = 'block';
        fileCount.textContent = '已选择 ' + selectedFiles.length + ' 个文件';
        fileNameList.innerHTML = '';

        selectedFiles.forEach(function (file) {
            var li = document.createElement('li');
            li.textContent = file.name + ' (' + formatSize(file.size) + ')';
            fileNameList.appendChild(li);
        });
    }

    // 清空选择
    btnClear.addEventListener('click', function () {
        selectedFiles = [];
        fileInput.value = '';
        updateFileList();
        hideResults();
    });

    // 快捷按钮
    document.querySelectorAll('.btn-preset').forEach(function (btn) {
        btn.addEventListener('click', function () {
            instruction.value = btn.getAttribute('data-text');
        });
    });

    // 提交处理
    btnProcess.addEventListener('click', function () {
        if (selectedFiles.length === 0) {
            showError('NO_FILE', '请选择一张或多张图片', 'Please select one or more images');
            return;
        }

        if (!instruction.value.trim()) {
            showError('NO_INSTRUCTION', '请输入图片处理指令', 'Please enter a processing instruction');
            return;
        }

        hideResults();
        processing.style.display = 'block';
        btnProcess.disabled = true;

        if (selectedFiles.length === 1) {
            processSingle();
        } else {
            processBatch();
        }
    });

    // 单张处理
    function processSingle() {
        var formData = new FormData();
        formData.append('image', selectedFiles[0]);
        formData.append('instruction', instruction.value.trim());
        var params = getCompressParams();
        formData.append('compress_mode', params.compress_mode);
        if (params.quality !== undefined) {
            formData.append('quality', params.quality);
        }

        fetch('/api/process-command', {
            method: 'POST',
            body: formData,
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                processing.style.display = 'none';
                btnProcess.disabled = false;

                if (data.success) {
                    showSingleResult(data);
                } else {
                    showError(
                        data.error_code || 'ERROR',
                        data.message || '处理失败',
                        data.suggestion || ''
                    );
                }
            })
            .catch(function (err) {
                processing.style.display = 'none';
                btnProcess.disabled = false;
                showError('NETWORK_ERROR', '网络错误: ' + err.message, '请检查服务是否启动');
            });
    }

    // 批量处理
    function processBatch() {
        var formData = new FormData();
        selectedFiles.forEach(function (file) {
            formData.append('images', file);
        });
        formData.append('instruction', instruction.value.trim());
        formData.append('zip_output', 'true');
        var params = getCompressParams();
        formData.append('compress_mode', params.compress_mode);
        if (params.quality !== undefined) {
            formData.append('quality', params.quality);
        }

        fetch('/api/batch-process-command', {
            method: 'POST',
            body: formData,
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                processing.style.display = 'none';
                btnProcess.disabled = false;

                if (data.success || data.success_count > 0) {
                    showBatchResult(data);
                } else {
                    showError(
                        data.error_code || 'BATCH_ERROR',
                        data.message || '批量处理失败',
                        data.suggestion || ''
                    );
                }
            })
            .catch(function (err) {
                processing.style.display = 'none';
                btnProcess.disabled = false;
                showError('NETWORK_ERROR', '网络错误: ' + err.message, '请检查服务是否启动');
            });
    }

    // 显示单张结果
    function showSingleResult(data) {
        var orig = data.original;
        var proc = data.processed;

        document.getElementById('origFilename').textContent = orig.filename;
        document.getElementById('origFormat').textContent = orig.format;
        document.getElementById('origSize').textContent = orig.width + ' x ' + orig.height;
        document.getElementById('origFileSize').textContent = formatKB(orig.file_size_kb);

        document.getElementById('procFilename').textContent = proc.filename;
        document.getElementById('procFormat').textContent = proc.format;
        document.getElementById('procSize').textContent = proc.width + ' x ' + proc.height;
        document.getElementById('procFileSize').textContent = formatKB(proc.file_size_kb);

        // 压缩率
        if (orig.file_size_kb > 0) {
            var ratio = ((1 - proc.file_size_kb / orig.file_size_kb) * 100).toFixed(1);
            document.getElementById('procRatio').textContent = ratio + '%';
        } else {
            document.getElementById('procRatio').textContent = '-';
        }

        // 预览图
        document.getElementById('procPreview').src = proc.preview_url;

        // 下载链接
        var downloadBtn = document.getElementById('procDownload');
        downloadBtn.href = proc.download_url;
        downloadBtn.download = proc.filename;

        resultSingle.style.display = 'block';
    }

    // 显示批量结果
    function showBatchResult(data) {
        document.getElementById('batchTotal').textContent = data.total_files;
        document.getElementById('batchSuccess').textContent = data.success_count;
        document.getElementById('batchFailed').textContent = data.failed_count;

        // ZIP 下载
        if (data.zip_download_url) {
            document.getElementById('batchZipDownload').href = data.zip_download_url;
            document.getElementById('batchZipDownload').download = data.zip_filename || 'batch-processed.zip';
            document.getElementById('batchZipArea').style.display = 'block';
        }

        // 成功列表
        var resultsList = document.getElementById('batchResultsList');
        resultsList.innerHTML = '';
        (data.results || []).forEach(function (item) {
            var div = document.createElement('div');
            div.className = 'batch-item';
            div.innerHTML =
                '<div class="batch-item-info">' +
                '<div class="name">' + escapeHtml(item.original_filename) + ' → ' + escapeHtml(item.output_filename) + '</div>' +
                '<div class="detail">' + item.final_format + ' | ' + item.final_width + 'x' + item.final_height + ' | ' + formatKB(item.final_file_size_kb) + '</div>' +
                '</div>' +
                '<a class="btn-download" href="' + item.download_url + '" download style="padding:5px 12px;font-size:12px;">下载</a>';
            resultsList.appendChild(div);
        });

        // 失败列表
        var failuresList = document.getElementById('batchFailuresList');
        failuresList.innerHTML = '';
        (data.failed_results || []).forEach(function (item) {
            var div = document.createElement('div');
            div.className = 'failure-item';
            div.innerHTML =
                '<div class="name">' + escapeHtml(item.original_filename) + '</div>' +
                '<div class="reason">' + escapeHtml(item.error_code) + ': ' + escapeHtml(item.message) + '</div>';
            failuresList.appendChild(div);
        });

        resultBatch.style.display = 'block';
    }

    // 显示错误
    function showError(code, message, suggestion) {
        document.getElementById('errorCode').textContent = code;
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSuggestion').textContent = suggestion;
        errorBox.style.display = 'block';
    }

    // 隐藏所有结果
    function hideResults() {
        errorBox.style.display = 'none';
        resultSingle.style.display = 'none';
        resultBatch.style.display = 'none';
        document.getElementById('batchZipArea').style.display = 'none';
    }

    // 工具函数
    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function formatKB(kb) {
        if (kb < 1) return (kb * 1024).toFixed(0) + ' B';
        if (kb < 1024) return kb.toFixed(1) + ' KB';
        return (kb / 1024).toFixed(1) + ' MB';
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
