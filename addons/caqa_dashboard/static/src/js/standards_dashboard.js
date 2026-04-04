/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";

export class StandardsDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.chartCanvasRef = useRef("standardsDistChart");
        this.chartInstance = null;
        this.state = useState({ data: null, loading: true });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => { this.renderChart(); });
    }

    async loadData() {
        try {
            this.state.loading = true;
            this.state.data = await this.orm.call("caqa.dashboard.service", "get_standards_payload", [{}]);
        } catch (error) {
            console.error("Standards Dashboard Load Error:", error);
            this.state.data = { kpis: {}, charts: { distribution: [] }, risks: [] };
        } finally {
            this.state.loading = false;
        }
    }

    renderChart() {
        if (!this.chartCanvasRef.el || !this.state.data?.charts?.distribution?.length) return;
        if (this.chartInstance) this.chartInstance.destroy();

        const chartData = this.state.data.charts.distribution;
        this.chartInstance = new Chart(this.chartCanvasRef.el, {
            type: 'bar',
            data: {
                labels: chartData.map(d => d.label),
                datasets: [{ label: 'العدد الإجمالي', data: chartData.map(d => d.value), backgroundColor: '#1A365D', borderRadius: 4 }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    }

    openVersions() {
        this.action.doAction({ type: "ir.actions.act_window", name: "نسخ المعايير", res_model: "caqa.standard.version", views: [[false, "list"], [false, "form"]], target: "current" });
    }

    openIndicators() {
        this.action.doAction({ type: "ir.actions.act_window", name: "المؤشرات", res_model: "caqa.standard.indicator", views: [[false, "list"], [false, "form"]], target: "current" });
    }
}
StandardsDashboard.template = "caqa_dashboard.StandardsDashboard";
registry.category("actions").add("caqa_dashboard.StandardsDashboard", StandardsDashboard);
