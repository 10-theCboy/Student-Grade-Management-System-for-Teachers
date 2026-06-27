document.addEventListener('DOMContentLoaded', function () {
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (a) {
        setTimeout(function () {
            a.classList.add('fade');
            setTimeout(function () { a.remove(); }, 300);
        }, 4000);
    });

    var sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    var currentPath = window.location.pathname;
    sidebarLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    /* ── Focus Window Expansion System ── */
    var overlay = document.getElementById('focusOverlay');
    var panel = document.getElementById('expandedPanel');
    var panelTitle = document.getElementById('panelTitle');
    var panelClose = document.getElementById('panelClose');
    var gradeSummary = document.getElementById('gradeSummary');
    var progressTimeline = document.getElementById('progressTimeline');
    var categoryBreakdown = document.getElementById('categoryBreakdown');
    var assignmentList = document.getElementById('assignmentList');
    var quizResults = document.getElementById('quizResults');
    var analyticsChart = document.getElementById('analyticsChart');
    var dashWrapper = document.getElementById('dashWrapper');
    var panelViewGrades = document.getElementById('panelViewGrades');
    var activeTab = null;

    var panelTabs = document.querySelectorAll('.panel-tab');
    var tabContents = {
        overview: document.getElementById('tabOverview'),
        assignments: document.getElementById('tabAssignments'),
        analytics: document.getElementById('tabAnalytics'),
        resources: document.getElementById('tabResources')
    };

    var isOpen = false;

    function openPanel(card) {
        if (isOpen) return;
        isOpen = true;

        var data = JSON.parse(card.getAttribute('data-course-data'));

        populatePanel(data, card);

        overlay.classList.add('active');
        if (dashWrapper) dashWrapper.classList.add('dimmed');
        panel.classList.add('active');
    }

    function closePanel() {
        if (!isOpen) return;
        isOpen = false;

        overlay.classList.remove('active');
        if (dashWrapper) dashWrapper.classList.remove('dimmed');
        panel.classList.remove('active');
    }

    function populatePanel(data, card) {
        panelTitle.textContent = data.code + ' — ' + data.name;

        /* View Grades link */
        var courseId = card.getAttribute('data-course-id');
        panelViewGrades.href = '/student/courses/' + courseId + '/grades';

        /* show loading */
        gradeSummary.innerHTML = '<p class="text-muted small mb-0">Loading...</p>';
        categoryBreakdown.innerHTML = '';
        progressTimeline.innerHTML = '';
        assignmentList.innerHTML = '';
        quizResults.innerHTML = '';
        analyticsChart.innerHTML = '';

        /* fetch real detail data */
        fetch('/student/api/courses/' + courseId + '/detail')
            .then(function (r) { return r.json(); })
            .then(function (detail) {
                var gradeBadgeClass = gradeClass(detail.grade);

                /* Grade summary */
                gradeSummary.innerHTML =
                    '<div class="grade-number">' + detail.total + '</div>' +
                    '<div class="grade-letter badge bg-' + gradeBadgeClass + '">' + detail.grade + '</div>' +
                    '<div class="grade-stats">' +
                        '<div class="grade-stat"><div class="stat-value">' + data.credits + '</div><div class="stat-label">Credits</div></div>' +
                        '<div class="grade-stat"><div class="stat-value">' + detail.progress + '%</div><div class="stat-label">Progress</div></div>' +
                    '</div>';

                /* Category breakdown */
                var catHtml = '<h6 class="fw-bold mb-2" style="font-size:13px;color:#334155;">Category Breakdown</h6>';
                (detail.categories || []).forEach(function (c) {
                    var pct = c.avg || 0;
                    var fillClass = pct >= 80 ? 'bg-success' : (pct >= 60 ? 'bg-warning' : 'bg-danger');
                    catHtml +=
                        '<div class="category-row">' +
                            '<div class="cat-name">' + c.name + ' (' + c.weight + '%)</div>' +
                            '<div class="cat-bar"><div class="cat-bar-fill ' + fillClass + '" style="width:' + pct + '%"></div></div>' +
                            '<div class="cat-score">' + (c.avg != null ? c.avg : '—') + '</div>' +
                        '</div>';
                });
                categoryBreakdown.innerHTML = catHtml;

                /* Progress timeline */
                var p = detail.progress;
                var milestones = [
                    { label: 'Started', done: true },
                    { label: 'Midterm', done: p >= 35 },
                    { label: '70% Mark', done: p >= 70 },
                    { label: 'Finals', done: p >= 85 },
                    { label: 'Complete', done: p >= 100 }
                ];
                var tlHtml = '<h6 class="fw-bold mb-2" style="font-size:13px;color:#334155;">Progress Timeline</h6>' +
                    '<div style="display:flex;gap:0;position:relative;padding:8px 0 4px">' +
                    '<div style="position:absolute;top:20px;left:8%;right:8%;height:3px;background:#e2e8f0;border-radius:2px;z-index:0"></div>';
                milestones.forEach(function (m, i) {
                    var done = m.done ? 'background:#16a34a;border-color:#16a34a' : 'background:#e2e8f0;border-color:#cbd5e1';
                    var labelWeight = m.done ? 'font-weight:600;color:#0f172a' : 'color:#94a3b8';
                    tlHtml +=
                        '<div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;z-index:1">' +
                            '<div style="width:12px;height:12px;border-radius:50%;border:2px solid;' + done + ';margin-bottom:4px;transition:all .3s ease"></div>' +
                            '<span style="font-size:10px;text-align:center;line-height:1.2;' + labelWeight + '">' + m.label + '</span>' +
                        '</div>';
                });
                tlHtml += '</div>';
                progressTimeline.innerHTML = tlHtml;

                /* Assignments & quizzes from real categories */
                var assignHtml = '';
                var quizHtml = '';
                (detail.categories || []).forEach(function (cat) {
                    (cat.items || []).forEach(function (item) {
                        var scoreClass = item.score != null ? (item.score >= 80 ? 'text-success' : (item.score >= 60 ? 'text-warning' : 'text-danger')) : 'text-muted';
                        var scoreDisplay = item.score != null ? item.score : '—';
                        var entry =
                            '<li>' +
                                '<div><span class="item-name">' + item.name + '</span><br><span class="item-class-avg">Class avg: ' + (item.classAvg != null ? item.classAvg : '—') + '</span></div>' +
                                '<div style="text-align:right"><span class="item-score ' + scoreClass + '">' + scoreDisplay + '</span><span class="item-max"> / ' + item.max + '</span></div>' +
                            '</li>';
                        if (cat.name.toLowerCase().indexOf('quiz') !== -1) {
                            quizHtml += entry;
                        } else {
                            assignHtml += entry;
                        }
                    });
                });
                assignmentList.innerHTML = assignHtml || '<p class="text-muted small">No assignments yet.</p>';
                quizResults.innerHTML = quizHtml || '<p class="text-muted small">No quiz results yet.</p>';

                /* Analytics chart */
                var chartHtml = '<div style="display:flex;align-items:flex-end;gap:8px;height:120px;padding:0 0.5rem">';
                (detail.categories || []).forEach(function (c) {
                    var pct = c.avg || 0;
                    var h = Math.max(20, pct * 1.2);
                    var color = pct >= 80 ? '#16a34a' : (pct >= 60 ? '#f59e0b' : '#ef4444');
                    var short = c.name.substring(0, 3).toUpperCase();
                    chartHtml +=
                        '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">' +
                            '<div style="width:100%;background:' + color + ';border-radius:4px 4px 0 0;height:' + h + 'px;transition:height .6s cubic-bezier(0.22,1,0.36,1)"></div>' +
                            '<span style="font-size:10px;color:#94a3b8;text-align:center">' + short + '</span>' +
                        '</div>';
                });
                chartHtml += '</div>';
                analyticsChart.innerHTML = chartHtml;
            })
            .catch(function () {
                gradeSummary.innerHTML = '<p class="text-muted small mb-0">Could not load data.</p>';
            });
    }

    function switchTab(tabId) {
        panelTabs.forEach(function (t) {
            t.classList.remove('active');
            if (t.getAttribute('data-tab') === tabId) t.classList.add('active');
        });
        Object.keys(tabContents).forEach(function (key) {
            tabContents[key].classList.remove('active');
        });
        if (tabContents[tabId]) tabContents[tabId].classList.add('active');
        activeTab = tabId;
    }

    /* tab click handlers */
    panelTabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            if (!isOpen) return;
            switchTab(this.getAttribute('data-tab'));
        });
    });

    /* card click */
    document.querySelectorAll('.course-card').forEach(function (card) {
        card.addEventListener('click', function (e) {
            if (e.target.closest('a') || e.target.closest('.btn')) return;
            openPanel(this);
        });
    });

    /* close button */
    panelClose.addEventListener('click', closePanel);

    /* overlay click closes */
    overlay.addEventListener('click', closePanel);

    /* escape key */
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen) closePanel();
    });

    function gradeClass(grade) {
        if (grade === 'A') return 'success';
        if (grade === 'B') return 'primary';
        if (grade === 'C') return 'warning text-dark';
        if (grade === 'D') return 'danger';
        return 'dark';
    }

    function generateCategoryData(data) {
        var avg = parseFloat(data.average) || 75;
        var cats = [
            { name: 'Homework', short: 'HW', score: Math.round(avg + (Math.random() * 10 - 5)) },
            { name: 'Quizzes', short: 'QZ', score: Math.round(avg + (Math.random() * 10 - 5)) },
            { name: 'Midterm', short: 'MT', score: Math.round(avg + (Math.random() * 8 - 4)) },
            { name: 'Final', short: 'FN', score: Math.round(avg + (Math.random() * 12 - 6)) },
            { name: 'Projects', short: 'PR', score: Math.round(avg + (Math.random() * 10 - 5)) }
        ];
        cats.forEach(function (c) {
            if (c.score > 100) c.score = 100;
            if (c.score < 0) c.score = 0;
        });
        return cats;
    }

    function generateMilestones(data) {
        var p = data.progress;
        return [
            { label: 'Started', done: true },
            { label: 'Midterm', done: p >= 35 },
            { label: '70% Mark', done: p >= 70 },
            { label: 'Finals', done: p >= 85 },
            { label: 'Complete', done: p >= 100 }
        ];
    }

    function generateAssignmentData(data) {
        var avg = parseFloat(data.average) || 75;
        return [
            { name: 'Assignment 1', score: Math.round(avg + (Math.random() * 8 - 4)), max: 100, classAvg: Math.round(70 + Math.random() * 15) },
            { name: 'Assignment 2', score: Math.round(avg + (Math.random() * 8 - 4)), max: 100, classAvg: Math.round(70 + Math.random() * 15) },
            { name: 'Assignment 3', score: Math.round(avg + (Math.random() * 8 - 4)), max: 100, classAvg: Math.round(70 + Math.random() * 15) },
            { name: 'Midterm Exam', score: Math.round(avg + (Math.random() * 10 - 5)), max: 100, classAvg: Math.round(65 + Math.random() * 15) },
            { name: 'Project', score: Math.round(avg + (Math.random() * 8 - 4)), max: 100, classAvg: Math.round(75 + Math.random() * 10) }
        ];
    }

    function generateQuizData(data) {
        var avg = parseFloat(data.average) || 75;
        return [
            { name: 'Quiz 1 — Chapter 1-3', score: Math.round(avg + (Math.random() * 10 - 5)), max: 50, classAvg: Math.round(35 + Math.random() * 10) },
            { name: 'Quiz 2 — Chapter 4-6', score: Math.round(avg + (Math.random() * 10 - 5)), max: 50, classAvg: Math.round(35 + Math.random() * 10) },
            { name: 'Quiz 3 — Chapter 7-9', score: Math.round(avg + (Math.random() * 10 - 5)), max: 50, classAvg: Math.round(35 + Math.random() * 10) }
        ];
    }
});