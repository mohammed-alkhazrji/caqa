/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";

export class CaqaDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.chartStateRef = useRef("appsByStateChart");
        this.chartSevRef = useRef("defByTypeChart");
        
        this.state = useState({ data: null, loading: true });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => { this.renderCharts(); });
    }

    async loadData() {
        try {
            this.state.loading = true;
            this.state.data = await this.orm.call("caqa.dashboard.service", "get_dashboard_payload", [{}]);
        } catch (error) {
            console.error("CAQA Dashboard Service Error:", error);
            this.state.data = { kpis: {}, charts: { apps_by_state: [], deficiencies_by_severity: [] }, alerts: [], recent_activity: [] };
        } finally {
            this.state.loading = false;
        }
    }

    renderCharts() {
        if (!this.state.data?.charts) return;
        if (this.chartStateRef.el && this.state.data.charts.apps_by_state?.length) {
            new Chart(this.chartStateRef.el, {
                type: 'doughnut',
                data: {
                    labels: this.state.data.charts.apps_by_state.map(d => d.label),
                    datasets: [{ data: this.state.data.charts.apps_by_state.map(d => d.value), backgroundColor: ['#1A365D', '#B87C19', '#2563eb', '#10b981', '#f59e0b', '#ef4444'], borderWidth: 0 }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
        if (this.chartSevRef.el && this.state.data.charts.deficiencies_by_severity?.length) {
            new Chart(this.chartSevRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.data.charts.deficiencies_by_severity.map(d => d.label),
                    datasets: [{ label: 'حالات عدم المطابقة', data: this.state.data.charts.deficiencies_by_severity.map(d => d.value), backgroundColor: '#ef4444', borderRadius: 4 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
            });
        }
    }

    openApplications() {
        this.action.doAction({ type: "ir.actions.act_window", name: "طلبات الاعتماد", res_model: "caqa.application", views: [[false, "list"], [false, "form"]], target: "current" });
    }

    openVisits() {
        this.action.doAction({ type: "ir.actions.act_window", name: "الزيارات الميدانية", res_model: "caqa.site.visit", views: [[false, "list"], [false, "form"]], target: "current" });
    }
}
CaqaDashboard.template = "caqa_dashboard.Dashboard";
registry.category("actions").add("caqa_dashboard.Dashboard", CaqaDashboard);
