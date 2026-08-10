// 引入 api_client.js 中的通訊與防抖函數
import { fetchSimulationData, debounce } from './api_client.js';

// 負責繪製 4 張 Plotly 圖表的函數
function renderPlotlyCharts(data) {
    const totalYears = data.npv_array.length; 
    const years = Array.from({length: totalYears}, (_, i) => i); 
    const physYears = Array.from({length: data.temp_array.length}, (_, i) => i + 1); 

    // 定義 4 張圖表共用的版面設定 (字體、背景透明、X 軸拉桿)
    const commonLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', 
        font: { color: '#86868b', family: '-apple-system, BlinkMacSystemFont, sans-serif', size: 10 },
        xaxis: { 
            title: { text: 'Operating Year', font: {size: 11} }, 
            gridcolor: 'rgba(255,255,255,0.05)', 
            range: [0, 32], // 預設顯示範圍 0~32 年
            // 開啟底部範圍滑桿 (Range Slider)，並設定為深灰色無邊框
            rangeslider: { visible: true, thickness: 0.06, bgcolor: '#2c2c2e', borderwidth: 0 } 
        },
        margin: { t: 30, l: 50, r: 15, b: 10 }, // 壓縮邊距以適應網格排版
        hovermode: 'x unified', // 設定游標懸停時顯示垂直對齊的數據標籤
        transition: { duration: 500, easing: 'cubic-in-out' } // 設定資料更新時的平滑動畫
    };

    // 1. 定義 NPV 圖表的資料軌跡與專屬設定
    const traceNPV = { x: years, y: data.npv_array, type: 'scatter', mode: 'lines', name: 'NPV', line: { color: '#30d158', width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(48, 209, 88, 0.1)' };
    const layoutNPV = { ...commonLayout, 
        title: { text: 'Cumulative Net Present Value (NPV)', font: { color: '#fff', size: 13 } },
        // 鎖定 Y 軸 (fixedrange: true)，並開啟紅色的 0 軸基準線
        yaxis: { title: {text: 'NTD', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', zeroline: true, zerolinecolor: '#ff453a', zerolinewidth: 2, fixedrange: true }
    };

    // 2. 定義流率圖表的資料軌跡與專屬設定
    const traceFlow = { x: physYears, y: data.flow_array, type: 'scatter', mode: 'lines', name: 'Flow Rate', line: { color: '#0a84ff', width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(10, 132, 255, 0.1)' };
    const layoutFlow = { ...commonLayout, 
        title: { text: 'CO2 Circulation Flow Rate (kg/s)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: 'kg/s', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true, rangemode: 'tozero' }
    };

    // 3. 定義溫度圖表的資料軌跡與專屬設定
    const traceTemp = { x: physYears, y: data.temp_array, type: 'scatter', mode: 'lines', name: 'Temperature', line: { color: '#ff9f0a', width: 3 } };
    const layoutTemp = { ...commonLayout, 
        title: { text: 'Bottom-hole Temp. Decline (°C)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: '°C', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true }
    };

    // 4. 定義壓力圖表的資料軌跡與專屬設定
    const tracePress = { x: physYears, y: data.pressure_array, type: 'scatter', mode: 'lines', name: 'Pressure', line: { color: '#bf5af2', width: 3 } };
    const layoutPress = { ...commonLayout, 
        title: { text: 'Bottom-hole Pressure Decline (kPa)', font: { color: '#fff', size: 13 } },
        yaxis: { title: {text: 'kPa', font: {size: 11}}, gridcolor: 'rgba(255,255,255,0.05)', fixedrange: true }
    };

    // 呼叫 Plotly.react 渲染 4 張圖表，開啟 scrollZoom 允許滾輪縮放 X 軸，開啟 responsive 允許自適應視窗大小
    Plotly.react('npv-chart', [traceNPV], layoutNPV, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('flow-chart', [traceFlow], layoutFlow, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('temp-chart', [traceTemp], layoutTemp, {displayModeBar: false, scrollZoom: true, responsive: true}); 
    Plotly.react('pressure-chart', [tracePress], layoutPress, {displayModeBar: false, scrollZoom: true, responsive: true}); 
}

// 負責更新整個儀表板數據的主函數
async function updateDashboard() {
    try {
        const data = await fetchSimulationData();
        if (!data) return;
        
        const updateText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.innerText = value;
        };
        
        // 更新 KPI 面板上的各項數值
        updateText('lcoe', (data.lcoe || 0).toFixed(2));
        updateText('irr', (data.irr || 0).toFixed(2) + '%');
        updateText('dpp', (data.dpp || 0).toFixed(1) + ' Yrs');
        
        // 計算年化碳排成本 (LCA 碳排量 * 碳價)
        const carbonCost = Math.round((data.annual_co2_tons || 0) * parseFloat(document.getElementById('carbon_price').value));
        updateText('annual_co2_tons', carbonCost.toLocaleString() + ' NTD');
        
        updateText('annual_power_mwh', Math.round(data.annual_power_mwh || 0).toLocaleString() + ' MWh');
        updateText('kpi_temp', (data.avg_temp_c || 0).toFixed(1) + ' °C');
        updateText('kpi_pressure', Math.round(data.avg_pressure_kpa || 0).toLocaleString() + ' kPa');
        updateText('kpi_flow', (data.avg_flow_kg_s || 0).toFixed(1) + ' kg/s');
        
        // 繪製圖表
        if (data.npv_array) renderPlotlyCharts(data);
    } catch (error) { 
        console.error("Dashboard update failed:", error); 
    }
}

// 將更新函數包裝上防抖機制 (延遲 200 毫秒執行)
const debouncedUpdate = debounce(updateDashboard, 200);

// 當網頁 DOM 結構載入完成後，執行初始化綁定
document.addEventListener('DOMContentLoaded', () => {
    // 綁定案場選擇下拉選單的變更事件
    const siteSelect = document.getElementById('site_id');
    if (siteSelect) {
        siteSelect.addEventListener('change', (e) => {
            const permSlider = document.getElementById('permeability_md');
            const poroSlider = document.getElementById('porosity');
            // 根據選擇的案場，動態調整滑桿的上下限與預設值
            if (e.target.value === 'KYS') {
                permSlider.min = 100; permSlider.max = 1500; permSlider.value = 1100;
                poroSlider.min = 0.01; poroSlider.max = 0.3; poroSlider.value = 0.15;
            }
            document.getElementById('val_permeability_md').innerText = permSlider.value + ' mD';
            document.getElementById('val_porosity').innerText = poroSlider.value + ' %';
            debouncedUpdate();
        });
    }

    const sliders = document.querySelectorAll('input[type="range"]');
    const units = {
        'permeability_md': ' mD', 'porosity': ' %', 'carbon_price': ' NTD',
        'fit_rate': ' NTD', 'discount_rate': ' %', 'capacity_factor': ' %'
    };

    // 為每個滑桿綁定 input 事件 (拖曳時即時觸發)
    sliders.forEach(input => {
        input.addEventListener('input', (e) => {
            const valDisplay = document.getElementById('val_' + e.target.id);
            if (valDisplay) {
                let displayVal = e.target.value;
                if (e.target.id === 'discount_rate' || e.target.id === 'capacity_factor') {
                    displayVal = (parseFloat(e.target.value) * 100).toFixed(2).replace(/\.00$/, '');
                }
                valDisplay.innerText = displayVal + units[e.target.id];
            }
            debouncedUpdate();
        });
    });
    
    // 網頁初次載入時，主動執行一次更新以繪製初始畫面
    updateDashboard();
});
