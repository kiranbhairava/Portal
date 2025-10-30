// LinkedIn Job Scraper Frontend Application
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentJobId = null;
    let jobsData = [];
    let sortField = 'posted_time';
    let sortDirection = 'desc';
    const SEARCH_HISTORY_KEY = 'linkedinJobSearchHistory';
    
    // DOM elements
    const jobSearchForm = document.getElementById('jobSearchForm');
    const jobStatus = document.getElementById('jobStatus');
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('resultsContainer');
    const jobsTableBody = document.getElementById('jobsTableBody');
    const jobCardsContainer = document.getElementById('jobCardsContainer');
    const noJobsMessage = document.getElementById('noJobsMessage');
    const noJobsMessageCard = document.getElementById('noJobsMessageCard');
    const exportCsv = document.getElementById('exportCsv');
    const exportExcel = document.getElementById('exportExcel');
    const activeFilters = document.getElementById('activeFilters');
    const searchHistoryList = document.getElementById('searchHistoryList');
    const noHistoryMessage = document.getElementById('noHistoryMessage');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const searchFilterInput = document.getElementById('jobSearchFilter');
    const cardSearchFilterInput = document.getElementById('jobCardSearchFilter');
    
    // Company logo colors for placeholder generation
    const logoColors = [
        '#0077B5', '#4285F4', '#FF9900', '#EA4335', '#34A853',
        '#FBBC05', '#FF6D01', '#5865F2', '#1ED760', '#FF0000'
    ];
    
    // Initialize the application
    initApp();
    
    // Event listeners
    jobSearchForm.addEventListener('submit', startJobSearch);
    exportCsv.addEventListener('click', handleExportCsv);
    exportExcel.addEventListener('click', handleExportExcel);
    clearHistoryBtn.addEventListener('click', clearSearchHistory);
    searchFilterInput.addEventListener('input', filterJobsList);
    cardSearchFilterInput.addEventListener('input', filterJobsCards);
    
    // Add event listeners to sortable table headers
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const field = header.dataset.sort;
            if (sortField === field) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortField = field;
                sortDirection = 'asc';
            }
            
            // Update sort icons
            document.querySelectorAll('.sortable i').forEach(icon => {
                icon.className = 'fas fa-sort text-muted ms-1';
            });
            
            const currentIcon = header.querySelector('i');
            currentIcon.className = sortDirection === 'asc' 
                ? 'fas fa-sort-up text-primary ms-1' 
                : 'fas fa-sort-down text-primary ms-1';
            
            renderJobsList(jobsData);
        });
    });
    
    // Application initialization
    function initApp() {
        loadSearchHistory();
        updateSearchHistoryUI();
    }
    
    // Start a new job search
    function startJobSearch(e) {
        e.preventDefault();
        
        // Get form values
        const keywords = document.getElementById('keywords').value.trim();
        const location = document.getElementById('location').value.trim();
        const limit = document.getElementById('limit').value;
        const experience = document.getElementById('experience').value;
        const jobType = document.getElementById('jobType').value;
        const headless = document.getElementById('headless').checked;
        const fast = document.getElementById('fast').checked;
        
        if (!keywords || !location) {
            alert('Please enter job keywords and location');
            return;
        }
        
        // Save search to history
        saveSearchToHistory({
            keywords,
            location,
            limit,
            experience,
            jobType,
            timestamp: Date.now()
        });
        
        // Prepare request body
        const requestBody = {
            keywords,
            location,
            limit: parseInt(limit),
            headless,
            fast
        };
        
        // Add optional parameters if selected
        if (experience) requestBody.experience = experience;
        if (jobType) requestBody.job_type = jobType;
        
        // Show job status and hide results
        showJobStatus();
        resultsContainer.classList.add('d-none');
        
        // Display active filters
        displayActiveFilters({
            keywords,
            location,
            limit,
            experience,
            jobType
        });
        
        // Send scrape request to API
        fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentJobId = data.job_id;
                pollJobStatus(data.job_id);
            } else {
                showError(`Failed to start job: ${data.error}`);
            }
        })
        .catch(error => {
            showError(`Error starting job: ${error.message}`);
        });
    }
    
    // Poll job status until complete
    function pollJobStatus(jobId) {
        const statusCheck = setInterval(() => {
            fetch(`/api/status/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const status = data.status;
                        updateJobStatusUI(status);
                        
                        if (status.status === 'completed' || status.status === 'error') {
                            clearInterval(statusCheck);
                            
                            if (status.status === 'completed') {
                                getJobResults(jobId);
                            }
                        }
                    } else {
                        clearInterval(statusCheck);
                        showError(`Failed to get job status: ${data.error}`);
                    }
                })
                .catch(error => {
                    clearInterval(statusCheck);
                    showError(`Error checking job status: ${error.message}`);
                });
        }, 1000);  // Check every second
    }
    
    // Get job results when scraping is complete
    function getJobResults(jobId) {
        fetch(`/api/results/${jobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Hide job status and show results
                    hideJobStatus();
                    resultsContainer.classList.remove('d-none');
                    
                    // Store jobs data and render
                    jobsData = data.results;
                    renderJobsList(jobsData);
                    renderJobsCards(jobsData);
                } else {
                    showError(`Failed to get job results: ${data.error}`);
                }
            })
            .catch(error => {
                showError(`Error getting job results: ${error.message}`);
            });
    }
    
    // Render jobs in list view
    function renderJobsList(jobs) {
        jobsTableBody.innerHTML = '';
        
        if (jobs.length === 0) {
            noJobsMessage.classList.remove('d-none');
            return;
        }
        
        noJobsMessage.classList.add('d-none');
        
        // Sort jobs before rendering
        const sortedJobs = sortJobs(jobs);
        
        sortedJobs.forEach(job => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>
                    <div class="fw-medium text-primary">${escapeHtml(job.title)}</div>
                </td>
                <td>${escapeHtml(job.company)}</td>
                <td>${escapeHtml(job.location)}</td>
                <td>${escapeHtml(job.posted_time)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-job-btn" data-job-index="${sortedJobs.indexOf(job)}">
                        <i class="far fa-eye"></i> View
                    </button>
                    <a href="${escapeHtml(job.job_url)}" class="btn btn-sm btn-outline-secondary" target="_blank">
                        <i class="fab fa-linkedin"></i>
                    </a>
                </td>
            `;
            
            jobsTableBody.appendChild(row);
        });
        
        // Add event listeners to view buttons
        document.querySelectorAll('.view-job-btn').forEach(button => {
            button.addEventListener('click', () => {
                const jobIndex = parseInt(button.dataset.jobIndex);
                openJobDetailsModal(sortedJobs[jobIndex]);
            });
        });
    }
    
    // Render jobs in card view
    function renderJobsCards(jobs) {
        jobCardsContainer.innerHTML = '';
        
        if (jobs.length === 0) {
            noJobsMessageCard.classList.remove('d-none');
            return;
        }
        
        noJobsMessageCard.classList.add('d-none');
        
        jobs.forEach(job => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4 job-card-item';
            
            // Get first letter of company name for logo placeholder
            const firstLetter = job.company.charAt(0).toUpperCase();
            const logoColor = logoColors[Math.floor(Math.random() * logoColors.length)];
            
            // Parse criteria into tags if available
            let criteriaHtml = '';
            if (job.criteria && job.criteria !== 'N/A') {
                const criteriaItems = job.criteria.split('|').map(item => item.trim());
                criteriaHtml = `
                    <div class="mt-2">
                        ${criteriaItems.map(item => `<span class="job-tag">${escapeHtml(item)}</span>`).join('')}
                    </div>
                `;
            }
            
            col.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex mb-3">
                            <div class="company-logo me-3" style="background-color: ${logoColor}10; color: ${logoColor}">
                                ${firstLetter}
                            </div>
                            <div>
                                <h5 class="job-title">${escapeHtml(job.title)}</h5>
                                <div class="company-name">${escapeHtml(job.company)}</div>
                                <div class="job-location">
                                    <i class="fas fa-map-marker-alt me-1"></i> ${escapeHtml(job.location)}
                                </div>
                                <div class="posted-time">
                                    <i class="far fa-clock me-1"></i> ${escapeHtml(job.posted_time)}
                                </div>
                            </div>
                        </div>
                        
                        ${criteriaHtml}
                        
                        <div class="job-card-footer">
                            <button class="btn btn-sm btn-primary view-job-card-btn" data-job-index="${jobs.indexOf(job)}">
                                View Details
                            </button>
                            <a href="${escapeHtml(job.job_url)}" class="btn btn-sm btn-outline-secondary" target="_blank">
                                <i class="fab fa-linkedin"></i> LinkedIn
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            jobCardsContainer.appendChild(col);
        });
        
        // Add event listeners to view buttons
        document.querySelectorAll('.view-job-card-btn').forEach(button => {
            button.addEventListener('click', () => {
                const jobIndex = parseInt(button.dataset.jobIndex);
                openJobDetailsModal(jobs[jobIndex]);
            });
        });
    }
    
    // Open job details modal
    function openJobDetailsModal(job) {
        const modal = new bootstrap.Modal(document.getElementById('jobDetailsModal'));
        
        // Set modal title
        document.getElementById('jobDetailsTitle').textContent = job.title;
        
        // Set job details
        document.getElementById('jobModalTitle').textContent = job.title;
        document.getElementById('jobModalCompany').textContent = job.company;
        document.getElementById('jobModalLocation').innerHTML = `<i class="fas fa-map-marker-alt me-1"></i> ${escapeHtml(job.location)}`;
        document.getElementById('jobModalPosted').innerHTML = `<i class="far fa-clock me-1"></i> ${escapeHtml(job.posted_time)}`;
        document.getElementById('jobModalUrl').href = job.job_url;
        
        // Get first letter of company name for logo
        const firstLetter = job.company.charAt(0).toUpperCase();
        const logoColor = logoColors[Math.floor(Math.random() * logoColors.length)];
        const logoElement = document.getElementById('jobModalLogo');
        logoElement.style.backgroundColor = `${logoColor}10`;
        logoElement.style.color = logoColor;
        logoElement.innerHTML = `${firstLetter}`;
        
        // Set job criteria
        const criteriaElement = document.getElementById('jobModalCriteria');
        criteriaElement.innerHTML = '';
        
        if (job.criteria && job.criteria !== 'N/A') {
            const criteriaItems = job.criteria.split('|').map(item => item.trim());
            criteriaItems.forEach(item => {
                const badge = document.createElement('span');
                badge.className = 'job-tag';
                badge.textContent = item;
                criteriaElement.appendChild(badge);
            });
        } else {
            criteriaElement.innerHTML = '<p class="text-muted small">No additional criteria available</p>';
        }
        
        // Set job description
        const descriptionElement = document.getElementById('jobModalDescription');
        if (job.description && job.description !== 'N/A') {
            descriptionElement.textContent = job.description;
        } else {
            descriptionElement.innerHTML = '<p class="text-muted">No description available. Please check the job on LinkedIn for more details.</p>';
        }
        
        modal.show();
    }
    
    // Handle export to CSV
    function handleExportCsv() {
        if (!currentJobId) return;
        
        fetch(`/api/export/csv/${currentJobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.file_url;
                } else {
                    alert(`Failed to export CSV: ${data.error}`);
                }
            })
            .catch(error => {
                alert(`Error exporting CSV: ${error.message}`);
            });
    }
    
    // Handle export to Excel
    function handleExportExcel() {
        if (!currentJobId) return;
        
        fetch(`/api/export/excel/${currentJobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.file_url;
                } else {
                    alert(`Failed to export Excel: ${data.error}`);
                }
            })
            .catch(error => {
                alert(`Error exporting Excel: ${error.message}`);
            });
    }
    
    // Update job status UI
    function updateJobStatusUI(status) {
        statusMessage.textContent = status.message;
        progressBar.style.width = `${status.progress}%`;
        progressBar.setAttribute('aria-valuenow', status.progress);
        
        if (status.status === 'error') {
            jobStatus.classList.remove('alert-info');
            jobStatus.classList.add('alert-danger');
        }
    }
    
    // Show error message
    function showError(message) {
        jobStatus.classList.remove('alert-info');
        jobStatus.classList.add('alert-danger');
        statusMessage.textContent = message;
        progressBar.style.width = '100%';
    }
    
    // Show job status
    function showJobStatus() {
        jobStatus.classList.remove('d-none', 'alert-danger');
        jobStatus.classList.add('alert-info');
        statusMessage.textContent = 'Initializing scraper...';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
    }
    
    // Hide job status
    function hideJobStatus() {
        jobStatus.classList.add('d-none');
    }
    
    // Display active filters
    function displayActiveFilters(filters) {
        activeFilters.innerHTML = '';
        
        // Always show keywords and location
        addFilterBadge('Keywords', filters.keywords);
        addFilterBadge('Location', filters.location);
        addFilterBadge('Limit', filters.limit);
        
        // Add optional filters if selected
        if (filters.experience) {
            const experienceLabel = document.querySelector(`#experience option[value="${filters.experience}"]`).textContent;
            addFilterBadge('Experience', experienceLabel);
        }
        
        if (filters.jobType) {
            const jobTypeLabel = document.querySelector(`#jobType option[value="${filters.jobType}"]`).textContent;
            addFilterBadge('Job Type', jobTypeLabel);
        }
    }
    
    // Add filter badge
    function addFilterBadge(label, value) {
        const badge = document.createElement('div');
        badge.className = 'filter-badge';
        badge.innerHTML = `
            <strong>${label}:</strong> ${escapeHtml(value)}
        `;
        activeFilters.appendChild(badge);
    }
    
    // Sort jobs based on current sort field and direction
    function sortJobs(jobs) {
        return [...jobs].sort((a, b) => {
            let valueA = a[sortField];
            let valueB = b[sortField];
            
            // Handle special case for posted_time (convert to comparable values)
            if (sortField === 'posted_time') {
                valueA = convertPostedTimeToHours(valueA);
                valueB = convertPostedTimeToHours(valueB);
            }
            
            if (valueA < valueB) {
                return sortDirection === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return sortDirection === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }
    
    // Convert posted time to hours for sorting
    function convertPostedTimeToHours(timeString) {
        if (!timeString) return 0;
        
        const match = timeString.match(/(\d+)\s+(minute|hour|day|week|month)s?/);
        if (!match) return 0;
        
        const value = parseInt(match[1]);
        const unit = match[2];
        
        switch (unit) {
            case 'minute': return value / 60;
            case 'hour': return value;
            case 'day': return value * 24;
            case 'week': return value * 24 * 7;
            case 'month': return value * 24 * 30;
            default: return 0;
        }
    }
    
    // Filter jobs list based on search input
    function filterJobsList() {
        const filterText = searchFilterInput.value.toLowerCase();
        const rows = jobsTableBody.querySelectorAll('tr');
        
        let visibleCount = 0;
        
        rows.forEach(row => {
            const jobTitle = row.querySelector('td:first-child').textContent.toLowerCase();
            const company = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const location = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            
            if (jobTitle.includes(filterText) || company.includes(filterText) || location.includes(filterText)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        if (visibleCount === 0) {
            noJobsMessage.classList.remove('d-none');
        } else {
            noJobsMessage.classList.add('d-none');
        }
    }
    
    // Filter jobs cards based on search input
    function filterJobsCards() {
        const filterText = cardSearchFilterInput.value.toLowerCase();
        const cards = document.querySelectorAll('.job-card-item');
        
        let visibleCount = 0;
        
        cards.forEach(card => {
            const jobTitle = card.querySelector('.job-title').textContent.toLowerCase();
            const company = card.querySelector('.company-name').textContent.toLowerCase();
            const location = card.querySelector('.job-location').textContent.toLowerCase();
            
            if (jobTitle.includes(filterText) || company.includes(filterText) || location.includes(filterText)) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        if (visibleCount === 0) {
            noJobsMessageCard.classList.remove('d-none');
        } else {
            noJobsMessageCard.classList.add('d-none');
        }
    }
    
    // Save search to history
    function saveSearchToHistory(search) {
        let history = getSearchHistory();
        
        // Add new search to history (limit to 10 items)
        history.unshift(search);
        if (history.length > 10) {
            history = history.slice(0, 10);
        }
        
        // Save to local storage
        localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(history));
        
        // Update UI
        updateSearchHistoryUI();
    }
    
    // Get search history from local storage
    function getSearchHistory() {
        const history = localStorage.getItem(SEARCH_HISTORY_KEY);
        return history ? JSON.parse(history) : [];
    }
    
    // Load search from history
    function loadSearchFromHistory(search) {
        document.getElementById('keywords').value = search.keywords;
        document.getElementById('location').value = search.location;
        document.getElementById('limit').value = search.limit;
        
        if (search.experience) {
            document.getElementById('experience').value = search.experience;
        }
        
        if (search.jobType) {
            document.getElementById('jobType').value = search.jobType;
        }
        
        // Trigger search
        document.getElementById('jobSearchForm').dispatchEvent(new Event('submit'));
        
        // Close modal
        const historyModal = bootstrap.Modal.getInstance(document.getElementById('historyModal'));
        historyModal.hide();
    }
    
    // Clear search history
    function clearSearchHistory() {
        localStorage.removeItem(SEARCH_HISTORY_KEY);
        updateSearchHistoryUI();
    }
    
    // Load search history
    function loadSearchHistory() {
        getSearchHistory();
    }
    
    // Update search history UI
    function updateSearchHistoryUI() {
        const history = getSearchHistory();
        searchHistoryList.innerHTML = '';
        
        if (history.length === 0) {
            noHistoryMessage.style.display = 'block';
            return;
        }
        
        noHistoryMessage.style.display = 'none';
        
        history.forEach((search, index) => {
            const item = document.createElement('div');
            item.className = 'search-history-item mb-2';
            
            // Format date
            const date = new Date(search.timestamp);
            const formattedDate = date.toLocaleString();
            
            // Optional parameters
            let optionalParams = [];
            if (search.experience) {
                optionalParams.push(`Experience: ${search.experience.replace('_', ' ')}`);
            }
            if (search.jobType) {
                optionalParams.push(`Job Type: ${search.jobType.replace('_', ' ')}`);
            }
            
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="fw-medium">${escapeHtml(search.keywords)} in ${escapeHtml(search.location)}</div>
                        <div class="small text-muted">
                            Limit: ${search.limit}
                            ${optionalParams.length > 0 ? ' • ' + optionalParams.join(' • ') : ''}
                        </div>
                        <div class="small text-muted">${formattedDate}</div>
                    </div>
                    <button class="btn btn-sm btn-primary load-search-btn" data-index="${index}">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
            `;
            
            searchHistoryList.appendChild(item);
        });
        
        // Add event listeners to load buttons
        document.querySelectorAll('.load-search-btn').forEach(button => {
            button.addEventListener('click', () => {
                const index = parseInt(button.dataset.index);
                loadSearchFromHistory(history[index]);
            });
        });
    }
    
    // Utility function to escape HTML
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
// ```

// And here's an updated `requirements.txt` file that includes Flask and other necessary packages:
// ```
// selenium>=4.11.2
// beautifulsoup4>=4.12.2
// pandas>=2.0.3
// webdriver-manager>=4.0.1
// openpyxl>=3.1.2
// flask>=2.0.1
// flask-cors>=3.0.10
// ```

// ## How to Set Up and Run the Application

// 1. **Save the files:**
//    - Save the HTML file as `simple_jobs_ui.html` in your project root directory
//    - Create a folder named `static/js` in your project root and save the JavaScript file as `app.js` in this folder
//    - Update your requirements.txt file with the additional dependencies

// 2. **Install dependencies:**
// ```
//    pip install -r requirements.txt
// ```

// 3. **Run the Flask server:**
// ```
//    python connector.py