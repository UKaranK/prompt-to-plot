document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('prompt-input');
    const btn = document.getElementById('analyze-btn');
    const statusContainer = document.getElementById('status-container');
    const errorContainer = document.getElementById('error-container');
    const errorText = document.getElementById('error-text');
    const resultsSection = document.getElementById('results-section');
    
    // Elements to populate
    const plotlyDiv = document.getElementById('plotly-div');
    const factText = document.getElementById('fact-text');
    const insightText = document.getElementById('insight-text');
    const actionText = document.getElementById('action-text');
    const sqlText = document.getElementById('sql-text');

    // Make Plotly dark mode by default to match our aesthetic
    const darkLayout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#f8fafc', family: 'Inter, sans-serif' },
        xaxis: { 
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)'
        },
        yaxis: { 
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)'
        }
    };

    btn.addEventListener('click', runQuery);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runQuery();
    });

    async function runQuery() {
        const prompt = input.value.trim();
        if (!prompt) return;

        // UI Reset and Loading State
        btn.disabled = true;
        input.disabled = true;
        errorContainer.classList.add('hidden');
        resultsSection.classList.add('hidden');
        statusContainer.classList.remove('hidden');
        Plotly.purge(plotlyDiv);

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to process request (HTTP Error)');
            }

            if (data.status === 'failed' || data.errors) {
                throw new Error(data.errors || 'The agent completely failed to process the request.');
            }

            // Populate Insights securely (using textContent to prevent XSS)
            const insights = data.insights || {};
            factText.textContent = insights.fact || 'No data facts found.';
            insightText.textContent = insights.insight || 'No insights generated.';
            actionText.textContent = insights.action || 'No actions recommended.';

            // Populate SQL Trace
            sqlText.textContent = data.generated_sql || 'No SQL generated.';

            // Render Visualization using Plotly.js natively
            const viz = data.visualization || {};
            if (viz.plotly_json) {
                const parsedFig = viz.plotly_json;
                // Deep merge our dark layout settings over the generated layout
                const layout = Object.assign({}, parsedFig.layout, darkLayout);
                Plotly.newPlot(plotlyDiv, parsedFig.data, layout, {responsive: true, displayModeBar: false});
            } else if (viz.chart_type === 'kpi' && viz.plotly_json) {
                const parsedFig = viz.plotly_json;
                const layout = Object.assign({}, parsedFig.layout, darkLayout);
                Plotly.newPlot(plotlyDiv, parsedFig.data, layout, {responsive: true, displayModeBar: false});
            } else {
                plotlyDiv.innerHTML = '<div style="color: #94a3b8; text-align: center; margin-top: 200px;">Table output generated. Please refer to raw data or adjust query for a chart.</div>';
            }

            // Show results
            resultsSection.classList.remove('hidden');

        } catch (err) {
            errorText.textContent = err.message;
            errorContainer.classList.remove('hidden');
        } finally {
            // Restore UI
            statusContainer.classList.add('hidden');
            btn.disabled = false;
            input.disabled = false;
            input.focus();
        }
    }
});
