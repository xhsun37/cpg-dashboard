// 定義防抖函數 (Debounce)，避免使用者快速拖曳滑桿時對伺服器造成過多請求
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => { 
            clearTimeout(timeout); 
            func(...args); 
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 定義非同步函數，負責向後端發送模擬請求
export async function fetchSimulationData() {
    try {
        // 取得網頁上的案場選擇下拉選單元素
        const siteIdElement = document.getElementById('site_id');
        if (!siteIdElement) {
            console.error("找不到 site_id 下拉選單，請確認 index.html 是否已存檔！");
            return null;
        }

        // 將網頁上所有滑桿的數值打包成 JSON 格式 (Payload)
        const payload = {
            site_id: siteIdElement.value, // 案場 ID 為字串，不需轉換
            permeability_md: parseFloat(document.getElementById('permeability_md').value),
            porosity: parseFloat(document.getElementById('porosity').value),
            carbon_price: parseFloat(document.getElementById('carbon_price').value),
            fit_rate: parseFloat(document.getElementById('fit_rate').value),
            discount_rate: parseFloat(document.getElementById('discount_rate').value),
            capacity_factor: parseFloat(document.getElementById('capacity_factor').value)
        };

        // 使用 fetch API 向 FastAPI 後端發送 POST 請求 (使用相對路徑 /api/simulate)
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        // 檢查 HTTP 回應狀態碼，若非 200 則拋出錯誤
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 將後端回傳的 JSON 字串解析為 JavaScript 物件並回傳
        return await response.json();
        
    } catch (error) {
        console.error("API 請求失敗:", error);
        return null;
    }
}
