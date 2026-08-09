// 負責與 FastAPI 後端通訊與防抖 (Debounce) 機制
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => { clearTimeout(timeout); func(...args); };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export async function fetchSimulationData() {
    try {
        // 1. 確保網頁上有這個下拉選單
        const siteIdElement = document.getElementById('site_id');
        if (!siteIdElement) {
            console.error("找不到 site_id 下拉選單，請確認 index.html 是否已存檔！");
            return null;
        }

        // 2. 打包資料 (注意：site_id 是字串，絕對不能加 parseFloat)
        const payload = {
            site_id: siteIdElement.value, 
            permeability_md: parseFloat(document.getElementById('permeability_md').value),
            porosity: parseFloat(document.getElementById('porosity').value),
            carbon_price: parseFloat(document.getElementById('carbon_price').value),
            fit_rate: parseFloat(document.getElementById('fit_rate').value),
            discount_rate: parseFloat(document.getElementById('discount_rate').value),
            capacity_factor: parseFloat(document.getElementById('capacity_factor').value)
        };

        // 3. 發送請求給後端 (改為相對路徑)
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error("API 請求失敗:", error);
        return null;
    }
}