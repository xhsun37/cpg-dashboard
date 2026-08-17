import { fetchSimulationData, debounce } from './api_client.js?v=5';

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

    // 【修改】刪除 Bottom-hole 文字
    const traceTemp = { x: physYears, y: data.temp_array, type: 'scatter', mode: 'lines', name: 'Temperature', line: { color: '#ff9f0a', width: 3 } };
    const layoutTemp = { ...commonLayout, 
        title: { text: 'Temp. Decline (°C)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: '°C', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true }
    };

    // 【修改】刪除 Bottom-hole 文字
    const tracePress = { x: physYears, y: data.pressure_array, type: 'scatter', mode: 'lines', name: 'Pressure', line: { color: '#bf5af2', width: 3 } };
    const layoutPress = { ...commonLayout, 
        title: { text: 'Pressure Decline (kPa)', font: { color: '#fff', size: 13 } },
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
        updateText('design_power_mw', (data.design_power_mw || 0).toFixed(2) + ' MW');
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
            if (e.target.value === 'KYS') {
                document.getElementById('permeability_md').value = 1100;
                document.getElementById('num_permeability_md').value = 1100;
                
                document.getElementById('porosity').value = 15;
                document.getElementById('num_porosity').value = 15;
            }
            debouncedUpdate();
        });
    }

    // 【新增】雙向綁定邏輯：滑桿與輸入框互相連動
    const params = ['permeability_md', 'porosity', 'carbon_price', 'fit_rate', 'discount_rate', 'capacity_factor'];
    
    params.forEach(param => {
        const slider = document.getElementById(param);
        const numInput = document.getElementById('num_' + param);

        // 當滑桿被拖曳時 -> 更新輸入框
        slider.addEventListener('input', (e) => {
            numInput.value = e.target.value;
            debouncedUpdate();
        });

        // 當輸入框被手動輸入時 -> 更新滑桿
        numInput.addEventListener('input', (e) => {
            let val = parseFloat(e.target.value);
            if (!isNaN(val)) {
                slider.value = val;
                debouncedUpdate();
            }
        });
    });
    
    updateDashboard();
});
