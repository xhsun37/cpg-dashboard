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

export async function fetchSimulationData() {
    try {
        const siteIdElement = document.getElementById('site_id');
        if (!siteIdElement) return null;

        // 【修改】將百分比欄位 (孔隙率、折現率、容量因子) 除以 100.0
        const payload = {
            site_id: siteIdElement.value, 
            permeability_md: parseFloat(document.getElementById('permeability_md').value),
            porosity: parseFloat(document.getElementById('porosity').value) / 100.0,
            carbon_price: parseFloat(document.getElementById('carbon_price').value),
            fit_rate: parseFloat(document.getElementById('fit_rate').value),
            discount_rate: parseFloat(document.getElementById('discount_rate').value) / 100.0,
            capacity_factor: parseFloat(document.getElementById('capacity_factor').value) / 100.0
        };

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
