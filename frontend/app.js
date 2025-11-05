// UPI Fraud Detection Frontend JavaScript

class FraudDetectionApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5001';
        this.transactions = [];
        this.stats = {
            total: 0,
            allowed: 0,
            verify: 0,
            blocked: 0
        };
        this.chart = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.populateTimeOptions();
        this.initChart();
        this.checkApiStatus();
        
        // Auto-generate transaction ID
        this.generateTransactionId();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('fraudDetectionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeTransaction();
        });

        // Real-time form validation
        const requiredFields = ['transactionId', 'amount', 'senderId', 'receiverId', 'transactionTime', 'receiverAge', 'receiverFraudReports'];
        requiredFields.forEach(fieldId => {
            document.getElementById(fieldId).addEventListener('input', this.validateForm);
        });
    }

    populateTimeOptions() {
        const timeSelect = document.getElementById('transactionTime');
        const currentHour = new Date().getHours();
        
        for (let hour = 0; hour < 24; hour++) {
            const option = document.createElement('option');
            option.value = hour;
            option.textContent = `${hour.toString().padStart(2, '0')}:00`;
            if (hour === currentHour) {
                option.selected = true;
            }
            timeSelect.appendChild(option);
        }
    }

    generateTransactionId() {
        const timestamp = Date.now().toString().slice(-6);
        const randomNum = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
        document.getElementById('transactionId').value = `TXN_${timestamp}${randomNum}`;
    }

    validateForm() {
        const form = document.getElementById('fraudDetectionForm');
        const submitBtn = document.getElementById('analyzeBtn');
        const isValid = form.checkValidity();
        
        submitBtn.disabled = !isValid;
        if (isValid) {
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-primary');
        } else {
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-secondary');
        }
    }

    async checkApiStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/health`);
            const data = await response.json();
            
            if (data.pipeline_loaded) {
                this.showNotification('API is online and ready', 'success');
            } else {
                this.showNotification('API is online but model not loaded', 'warning');
            }
        } catch (error) {
            this.showNotification('API is offline. Please start the backend server.', 'danger');
            console.error('API Status Error:', error);
        }
    }

    async analyzeTransaction() {
        const form = document.getElementById('fraudDetectionForm');
        const submitBtn = document.getElementById('analyzeBtn');
        
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // Show loading state
        submitBtn.classList.add('loading');
        
        try {
            const transactionData = this.getTransactionData();
            
            const response = await fetch(`${this.apiBaseUrl}/api/detect-fraud`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(transactionData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Process and display result
            this.displayResult(result, transactionData);
            this.addToHistory(result, transactionData);
            this.updateStats(result);
            this.updateChart();
            
            // Generate new transaction ID for next transaction
            this.generateTransactionId();
            
            this.showNotification('Transaction analyzed successfully!', 'success');
            
        } catch (error) {
            console.error('Analysis Error:', error);
            this.showNotification(`Analysis failed: ${error.message}`, 'danger');
        } finally {
            // Hide loading state
            submitBtn.classList.remove('loading');
        }
    }

    getTransactionData() {
        return {
            transaction_id: document.getElementById('transactionId').value,
            sender_id: document.getElementById('senderId').value,
            receiver_id: document.getElementById('receiverId').value,
            amount: parseFloat(document.getElementById('amount').value),
            transaction_time: parseInt(document.getElementById('transactionTime').value),
            transaction_frequency_last_24h: parseInt(document.getElementById('frequency24h').value) || 3,
            avg_amount_last_week: parseFloat(document.getElementById('avgAmountWeek').value) || 2000,
            transaction_type: document.getElementById('transactionType').value,
            device_id: `device_${Math.floor(Math.random() * 1000)}`,
            os_version: document.getElementById('osVersion').value,
            ip_address: `192.168.1.${Math.floor(Math.random() * 254) + 1}`,
            current_latitude: 28.6139 + (Math.random() - 0.5) * 0.1,
            current_longitude: 77.2090 + (Math.random() - 0.5) * 0.1,
            geo_distance_from_last_txn: parseFloat(document.getElementById('geoDistance').value) || 5.2,
            receiver_age_days: parseInt(document.getElementById('receiverAge').value),
            receiver_fraud_reports: parseInt(document.getElementById('receiverFraudReports').value),
            unique_senders_to_receiver: Math.floor(Math.random() * 500) + 50,
            time_between_upi_open_and_pay: parseFloat(document.getElementById('openToPay').value) || 25,
            otp_entry_delay: parseFloat(document.getElementById('otpDelay').value) || 12,
            is_unusual_hour: this.isUnusualHour(parseInt(document.getElementById('transactionTime').value)),
            amount_deviation_from_avg: Math.abs(parseFloat(document.getElementById('amount').value) - (parseFloat(document.getElementById('avgAmountWeek').value) || 2000)) / (parseFloat(document.getElementById('avgAmountWeek').value) || 2000),
            timestamp: new Date().toISOString().slice(0, 19).replace('T', ' ')
        };
    }

    isUnusualHour(hour) {
        // Consider 10 PM to 6 AM as unusual hours
        return (hour >= 22 || hour <= 6) ? 1 : 0;
    }

    displayResult(result, transactionData) {
        const resultCard = document.getElementById('resultCard');
        const resultContent = document.getElementById('resultContent');
        
        if (result.error) {
            resultContent.innerHTML = this.createErrorResult(result.error);
            resultCard.className = 'card mb-4 result-card result-block';
        } else {
            const fraudData = result.fraud_detection;
            const actionData = result.action_response;
            
            resultContent.innerHTML = this.createSuccessResult(fraudData, actionData, transactionData);
            
            // Set card style based on action
            let cardClass = 'card mb-4 result-card';
            switch (actionData.action) {
                case 'ALLOW':
                    cardClass += ' result-allow';
                    break;
                case 'VERIFY':
                    cardClass += ' result-verify';
                    break;
                case 'BLOCK':
                    cardClass += ' result-block';
                    break;
            }
            resultCard.className = cardClass;
        }
        
        resultCard.style.display = 'block';
        resultCard.classList.add('fade-in');
        
        // Scroll to result
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    createSuccessResult(fraudData, actionData, transactionData) {
        const actionIcon = this.getActionIcon(actionData.action);
        const riskBadge = this.getRiskBadge(fraudData.risk_level);
        const scorePercentage = (fraudData.fraud_score * 100).toFixed(2);
        
        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="d-flex align-items-center mb-3">
                        <div class="me-3">
                            ${actionIcon}
                        </div>
                        <div>
                            <h4 class="mb-1">${actionData.action}</h4>
                            <p class="text-muted mb-0">${actionData.message}</p>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <span class="fw-semibold">Fraud Score</span>
                            <span>${scorePercentage}%</span>
                        </div>
                        <div class="progress progress-custom">
                            <div class="progress-bar progress-bar-custom bg-${this.getScoreColor(fraudData.fraud_score)}" 
                                 style="width: ${scorePercentage}%"></div>
                        </div>
                    </div>
                    
                    <div class="row text-center">
                        <div class="col-4">
                            <div class="border-end">
                                <div class="fw-bold">${riskBadge}</div>
                                <small class="text-muted">Risk Level</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="border-end">
                                <div class="fw-bold">${fraudData.confidence}</div>
                                <small class="text-muted">Confidence</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold">₹${transactionData.amount.toLocaleString()}</div>
                            <small class="text-muted">Amount</small>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <h6 class="fw-semibold mb-2">Analysis Details</h6>
                    <div class="bg-light rounded-3 p-3 mb-3">
                        <small class="text-muted">${fraudData.reasoning}</small>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <strong>Transaction ID:</strong><br>
                            <code class="small">${transactionData.transaction_id}</code>
                        </div>
                        <div class="col-6">
                            <strong>Processed At:</strong><br>
                            <small>${new Date().toLocaleTimeString()}</small>
                        </div>
                    </div>
                    
                    ${actionData.next_steps ? `
                        <div class="mt-3">
                            <strong>Next Steps:</strong>
                            <ul class="small mb-0 mt-1">
                                ${actionData.next_steps.map(step => `<li>${step.replace('_', ' ').toUpperCase()}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    createErrorResult(error) {
        return `
            <div class="text-center">
                <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                <h4 class="text-danger">Analysis Failed</h4>
                <p class="text-muted">${error}</p>
                <small class="text-muted">Please check your input data and try again.</small>
            </div>
        `;
    }

    getActionIcon(action) {
        const icons = {
            'ALLOW': '<i class="fas fa-check-circle text-success fa-2x"></i>',
            'VERIFY': '<i class="fas fa-exclamation-triangle text-warning fa-2x"></i>',
            'BLOCK': '<i class="fas fa-ban text-danger fa-2x"></i>'
        };
        return icons[action] || '<i class="fas fa-question-circle text-secondary fa-2x"></i>';
    }

    getRiskBadge(riskLevel) {
        const badges = {
            'LOW': '<span class="risk-badge risk-low">LOW</span>',
            'MEDIUM': '<span class="risk-badge risk-medium">MEDIUM</span>',
            'HIGH': '<span class="risk-badge risk-high">HIGH</span>'
        };
        return badges[riskLevel] || '<span class="risk-badge">UNKNOWN</span>';
    }

    getScoreColor(score) {
        if (score < 0.4) return 'success';
        if (score < 0.7) return 'warning';
        return 'danger';
    }

    addToHistory(result, transactionData) {
        this.transactions.unshift({
            ...result,
            transactionData,
            timestamp: new Date()
        });
        
        // Keep only last 10 transactions
        if (this.transactions.length > 10) {
            this.transactions = this.transactions.slice(0, 10);
        }
        
        this.updateTransactionHistory();
    }

    updateTransactionHistory() {
        const historyContainer = document.getElementById('transactionHistory');
        
        if (this.transactions.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>No transactions analyzed yet</p>
                </div>
            `;
            return;
        }
        
        const historyHtml = this.transactions.map((tx, index) => {
            const actionData = tx.action_response;
            const fraudData = tx.fraud_detection;
            const txData = tx.transactionData;
            
            return `
                <div class="border-bottom p-3 ${index === 0 ? 'bg-light' : ''}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-1">
                                <strong class="me-2">${txData.transaction_id}</strong>
                                ${this.getRiskBadge(fraudData.risk_level)}
                            </div>
                            <div class="small text-muted mb-1">
                                ₹${txData.amount.toLocaleString()} • ${txData.sender_id} → ${txData.receiver_id}
                            </div>
                            <div class="small text-muted">
                                ${tx.timestamp.toLocaleTimeString()}
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="mb-1">
                                ${this.getActionIcon(actionData.action).replace('fa-2x', 'fa-lg')}
                            </div>
                            <div class="small fw-bold">
                                ${(fraudData.fraud_score * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        historyContainer.innerHTML = historyHtml;
    }

    updateStats(result) {
        this.stats.total++;
        
        const action = result.action_response.action;
        switch (action) {
            case 'ALLOW':
                this.stats.allowed++;
                break;
            case 'VERIFY':
                this.stats.verify++;
                break;
            case 'BLOCK':
                this.stats.blocked++;
                break;
        }
        
        // Update DOM
        document.getElementById('totalTransactions').textContent = this.stats.total;
        document.getElementById('allowedTransactions').textContent = this.stats.allowed;
        document.getElementById('verifyTransactions').textContent = this.stats.verify;
        document.getElementById('blockedTransactions').textContent = this.stats.blocked;
    }

    initChart() {
        // Main Analytics Chart - BIGGER SIZE
        const ctx = document.getElementById('analyticsChart').getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['✅ Allowed', '⚠️ Verify Required', '🚫 Blocked'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgba(5, 150, 105, 0.9)',
                        'rgba(217, 119, 6, 0.9)',
                        'rgba(220, 38, 38, 0.9)'
                    ],
                    borderColor: [
                        'rgba(5, 150, 105, 1)',
                        'rgba(217, 119, 6, 1)',
                        'rgba(220, 38, 38, 1)'
                    ],
                    borderWidth: 4,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: 20
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 25,
                            font: {
                                size: 14,
                                weight: 'bold'
                            },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        titleFont: {
                            size: 16,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 14
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                elements: {
                    arc: {
                        borderWidth: 4
                    }
                }
            }
        });

        // Initialize Risk Distribution Chart
        this.initRiskChart();
        
        // Initialize Timeline Chart
        this.initTimelineChart();
    }

    initRiskChart() {
        const riskCtx = document.getElementById('riskChart')?.getContext('2d');
        if (riskCtx) {
            this.riskChart = new Chart(riskCtx, {
                type: 'bar',
                data: {
                    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical'],
                    datasets: [{
                        label: 'Transaction Count',
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(124, 45, 18, 0.8)'
                        ],
                        borderColor: [
                            'rgba(16, 185, 129, 1)',
                            'rgba(245, 158, 11, 1)',
                            'rgba(239, 68, 68, 1)',
                            'rgba(124, 45, 18, 1)'
                        ],
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            titleFont: { size: 16 },
                            bodyFont: { size: 14 },
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: { size: 12, weight: 'bold' }
                            }
                        }
                    }
                }
            });
        }
    }

    initTimelineChart() {
        const timelineCtx = document.getElementById('timelineChart')?.getContext('2d');
        if (timelineCtx) {
            this.timelineChart = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Fraud Score Trend',
                        data: [],
                        borderColor: 'rgba(239, 68, 68, 1)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                font: { size: 14, weight: 'bold' }
                            }
                        },
                        tooltip: {
                            titleFont: { size: 16 },
                            bodyFont: { size: 14 },
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                font: { size: 12 }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: { size: 12 }
                            }
                        }
                    }
                }
            });
        }
    }

    updateChart() {
        // Update main analytics chart
        if (this.chart) {
            this.chart.data.datasets[0].data = [
                this.stats.allowed,
                this.stats.verify,
                this.stats.blocked
            ];
            this.chart.update('active');
        }

        // Update risk distribution chart
        if (this.riskChart && this.transactions.length > 0) {
            const riskCounts = [0, 0, 0, 0]; // Low, Medium, High, Critical
            
            this.transactions.forEach(tx => {
                const score = tx.fraud_detection?.fraud_score || 0;
                if (score < 0.3) riskCounts[0]++;
                else if (score < 0.6) riskCounts[1]++;
                else if (score < 0.8) riskCounts[2]++;
                else riskCounts[3]++;
            });
            
            this.riskChart.data.datasets[0].data = riskCounts;
            this.riskChart.update('active');
        }

        // Update timeline chart
        if (this.timelineChart && this.transactions.length > 0) {
            const recentTransactions = this.transactions.slice(-10); // Last 10 transactions
            const labels = recentTransactions.map((tx, index) => `TX-${index + 1}`);
            const scores = recentTransactions.map(tx => tx.fraud_detection?.fraud_score || 0);
            
            this.timelineChart.data.labels = labels;
            this.timelineChart.data.datasets[0].data = scores;
            this.timelineChart.update('active');
        }
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear all transaction history?')) {
            this.transactions = [];
            this.stats = { total: 0, allowed: 0, verify: 0, blocked: 0 };
            
            this.updateTransactionHistory();
            this.updateStats({ action_response: { action: 'CLEAR' } });
            this.updateChart();
            
            // Reset stats display
            document.getElementById('totalTransactions').textContent = '0';
            document.getElementById('allowedTransactions').textContent = '0';
            document.getElementById('verifyTransactions').textContent = '0';
            document.getElementById('blockedTransactions').textContent = '0';
            
            // Hide result card
            document.getElementById('resultCard').style.display = 'none';
            
            this.showNotification('History cleared successfully', 'info');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    async processBatch() {
        const fileInput = document.getElementById('csvFile');
        const batchBtn = document.getElementById('batchBtn');
        
        if (!fileInput.files.length) {
            this.showNotification('Please select a CSV file', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        
        // Simple CSV validation
        if (!file.name.toLowerCase().endsWith('.csv')) {
            this.showNotification('Please select a valid CSV file', 'warning');
            return;
        }
        
        batchBtn.disabled = true;
        batchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
        
        try {
            // For demo purposes, we'll simulate batch processing
            // In a real application, you'd parse the CSV and send to the API
            
            this.showNotification('Batch processing started...', 'info');
            
            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Generate some sample results
            const sampleResults = this.generateSampleBatchResults(5);
            
            // Process each result
            sampleResults.forEach((result, index) => {
                setTimeout(() => {
                    this.addToHistory(result.result, result.transactionData);
                    this.updateStats(result.result);
                    if (index === sampleResults.length - 1) {
                        this.updateChart();
                        this.showNotification(`Batch processing completed! Processed ${sampleResults.length} transactions.`, 'success');
                    }
                }, (index + 1) * 500);
            });
            
        } catch (error) {
            console.error('Batch processing error:', error);
            this.showNotification('Batch processing failed', 'danger');
        } finally {
            batchBtn.disabled = false;
            batchBtn.innerHTML = '<i class="fas fa-upload me-1"></i> Process Batch';
        }
    }

    generateSampleBatchResults(count) {
        const results = [];
        
        for (let i = 0; i < count; i++) {
            const transactionData = {
                transaction_id: `BATCH_${Date.now()}_${i}`,
                sender_id: `user${Math.floor(Math.random() * 1000)}@upi`,
                receiver_id: `merchant${Math.floor(Math.random() * 1000)}@upi`,
                amount: Math.floor(Math.random() * 50000) + 100,
                transaction_time: Math.floor(Math.random() * 24),
                receiver_age_days: Math.floor(Math.random() * 365) + 1,
                receiver_fraud_reports: Math.floor(Math.random() * 5)
            };
            
            // Simulate different results
            const fraudScore = Math.random();
            let action, riskLevel;
            
            if (fraudScore < 0.4) {
                action = 'ALLOW';
                riskLevel = 'LOW';
            } else if (fraudScore < 0.7) {
                action = 'VERIFY';
                riskLevel = 'MEDIUM';
            } else {
                action = 'BLOCK';
                riskLevel = 'HIGH';
            }
            
            const result = {
                fraud_detection: {
                    fraud_score: fraudScore,
                    risk_level: riskLevel,
                    action: action,
                    reasoning: `Batch processed transaction with fraud score: ${fraudScore.toFixed(4)}`,
                    confidence: Math.random() * 0.5 + 0.5
                },
                action_response: {
                    action: action,
                    status: action === 'ALLOW' ? 'success' : action === 'VERIFY' ? 'pending' : 'blocked',
                    message: `Transaction ${action.toLowerCase()}ed by batch processing`
                }
            };
            
            results.push({ result, transactionData });
        }
        
        return results;
    }

    downloadSampleCSV() {
        const csvContent = `transaction_id,sender_id,receiver_id,amount,transaction_time,receiver_age_days,receiver_fraud_reports
SAMPLE_001,user123@upi,merchant456@upi,2500,14,365,0
SAMPLE_002,user456@upi,merchant789@upi,8000,22,15,1
SAMPLE_003,user789@upi,merchant123@upi,50000,3,2,8
SAMPLE_004,user321@upi,merchant654@upi,5,2,1,0
SAMPLE_005,user654@upi,merchant987@upi,25000,1,5,3`;
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sample_transactions.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Sample CSV downloaded successfully', 'success');
    }
}

// Global functions for inline event handlers
function fillSampleData() {
    // Fill form with sample data
    document.getElementById('senderId').value = 'user123@upi';
    document.getElementById('receiverId').value = 'merchant456@upi';
    document.getElementById('amount').value = '2500';
    document.getElementById('transactionTime').value = new Date().getHours();
    document.getElementById('receiverAge').value = '365';
    document.getElementById('receiverFraudReports').value = '0';
    document.getElementById('geoDistance').value = '5.2';
    
    app.showNotification('Sample data filled successfully', 'info');
}

function clearHistory() {
    app.clearHistory();
}

function processBatch() {
    app.processBatch();
}

function downloadSampleCSV() {
    app.downloadSampleCSV();
}

// Initialize the application when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', function() {
    app = new FraudDetectionApp();
});