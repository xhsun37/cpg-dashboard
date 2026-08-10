import { fetchSimulationData, debounce } from './api_client.js';

function renderPlotlyCharts(data) {
    const totalYears = data.npv_array.length; 
    const years = Array.from({length: totalYears}, (_, i) => i); 
    const physYears = Array.from({length: data.temp_array.length}, (_, i) => i + 1); 

    const commonLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', 
        font: { color: '#86868b', family: '-apple-system, BlinkMacSystemFont, sans-serif', size: 10 },
        xaxis: { 
            title: { text: 'Operating Year', font: {size: 11} }, 
            gridcolor: 'rgba(255,255,255,0.05)', 
            range: [0, 32], 
            rangeslider: { visible: true, thickness: 0.06, bgcolor: '#2c2c2e', borderwidth: 0 } 
        },
        margin: { t: 30, l: 50, r: 15, b: 10 }, 
        hovermode: 'x unified',
        transition: { duration: 500, easing: 'cubic-in-out' }
    };

    const traceNPV = { x: years, y: data.npv_array, type: 'scatter', mode: 'lines', name: 'NPV', line: { color: '#30d158', width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(48, 209, 88, 0.1)' };
    const layoutNPV = { ...commonLayout, 
        title: { text: 'Cumulative Net Present Value (NPV)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: 'NTD', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', zeroline: true, zerolinecolor: '#ff453a', zerolinewidth: 2, fixedrange: true }
    };

    const traceFlow = { x: physYears, y: data.flow_array, type: 'scatter', mode: 'lines', name: 'Flow Rate', line: { color: '#0a84ff', width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(10, 132, 255, 0.1)' };
    const layoutFlow = { ...commonLayout, 
        title: { text: 'CO2 Circulation Flow Rate (kg/s)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: 'kg/s', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true, rangemode: 'tozero' }
    };

    const traceTemp = { x: physYears, y: data.temp_array, type: 'scatter', mode: 'lines', name: 'Temperature', line: { color: '#ff9f0a', width: 3 } };
    const layoutTemp = { ...commonLayout, 
        title: { text: 'Bottom-hole Temp. Decline (°C)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: '°C', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true }
    };

    const tracePress = { x: physYears, y: data.pressure_array, type: 'scatter', mode: 'lines', name: 'Pressure', line: { color: '#bf5af2', width: 3 } };
    const layoutPress = { ...commonLayout, 
        title: { text: 'Bottom-hole Pressure Decline (kPa)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: 'kPa', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true }
    };

    Plotly.react('npv-chart', [traceNPV], layoutNPV, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('flow-chart', [traceFlow], layoutFlow, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('temp-chart', [traceTemp], layoutTemp, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('pressure-chart', [tracePress], layoutPress, {displayModeBar: false, scrollZoom: true, responsive: true}); 
}

async function updateDashboard() {
    try {
        const data = await fetchSimulationData();
        if (!data) return;
        
        const updateText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.innerText = value;
        };
        
        updateText('lcoe', (data.lcoe || 0).toFixed(2));
        updateText('irr', (data.irr || 0).toFixed(2) + '%');
        updateText('dpp', (data.dpp || 0).toFixed(1) + ' Yrs');
        
        const carbonCost = Math.round((data.annual_co2_tons || 0) * parseFloat(document.getElementById('carbon_price').value));
        updateText('annual_co2_tons', carbonCost.toLocaleString() + ' NTD');
        
        updateText('annual_power_mwh', Math.round(data.annual_power_mwh || 0).toLocaleString() + ' MWh');
        updateText('kpi_temp', (data.avg_temp_c || 0).toFixed(1) + ' °C');
        updateText('kpi_pressure', Math.round(data.avg_pressure_kpa || 0).toLocaleString() + ' kPa');
        updateText('kpi_flow', (data.avg_flow_kg_s || 0).toFixed(1) + ' kg/s');
        
        if (data.npv_array) renderPlotlyCharts(data);
    } catch (error) { 
        console.error("Dashboard update failed:", error); 
    }
}

const debouncedUpdate = debounce(updateDashboard, 200);

document.addEventListener('DOMContentLoaded', () => {
    const siteSelect = document.getElementById('site_id');
    if (siteSelect) {
        siteSelect.addEventListener('change', (e) => {
            const permSlider = document.getElementById('permeability_md');
            const poroSlider = document.getElementById('porosity');
            if (e.target.value === 'KYS') {
                permSlider.min = 100; permSlider.max = 1500; permSlider.value = 1100;
                poroSlider.min = 0.01; poroSlider.max = 0.3; poroSlider.value = 0.15;
            }
            document.getElementById('val_permeability_md').innerText = permSlider.value + ' mD';
            
            // 【修正 1】切換案場時，孔隙率也要乘以 100 顯示
            const poroPercent = Number((parseFloat(poroSlider.value) * 100).toFixed(2)).toString();
            document.getElementById('val_porosity').innerText = poroPercent + ' %';
            
            debouncedUpdate();
        });
    }

    const sliders = document.querySelectorAll('input[type="range"]');
    const units = {
        'permeability_md': ' mD', 'porosity': ' %', 'carbon_price': ' NTD',
        'fit_rate': ' NTD', 'discount_rate': ' %', 'capacity_factor': ' %'
    };

    sliders.forEach(input => {
        input.addEventListener('input', (e) => {
            const valDisplay = document.getElementById('val_' + e.target.id);
            if (valDisplay) {
                let displayVal = e.target.value;
                
                // 【修正 2】更安全、更乾淨的百分比轉換寫法
                if (e.target.id === 'discount_rate' || e.target.id === 'capacity_factor' || e.target.id === 'porosity') {
                    displayVal = Number((parseFloat(e.target.value) * 100).toFixed(2)).toString();
                }
                
                valDisplay.innerText = displayVal + units[e.target.id];
            }
            debouncedUpdate();
        });
    });
    updateDashboard();
});
