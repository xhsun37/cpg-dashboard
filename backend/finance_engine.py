import numpy as np

# 自定義高穩定性 IRR 計算器 (二分逼近法)，解決 30 年期高階多項式發散問題
def calculate_stable_irr(cash_flows):
    if all(cf >= 0 for cf in cash_flows) or all(cf <= 0 for cf in cash_flows): return 0.0
    def calc_npv(rate): return sum(cf / ((1.0 + rate) ** i) for i, cf in enumerate(cash_flows))
    low, high = -0.99, 2.0 
    if calc_npv(low) * calc_npv(high) > 0: return 0.0
    for _ in range(100):
        mid = (low + high) / 2.0
        val = calc_npv(mid)
        if abs(val) < 1e-4: return mid
        if val > 0: low = mid  
        else: high = mid 
    return (low + high) / 2.0

# 財務經濟計算主函數
def calculate_economics(carbon_price_ntd: float, fit_rate_ntd: float, discount_rate: float, power_mwh_array: list, co2_tons_array: list, capacity_factor: float):
    years = 30
    r = discount_rate
    
    field_power_mwh_array = np.array(power_mwh_array)
    field_co2_tons_array = np.array(co2_tons_array)

    # 擷取第 11~30 年 (索引 10:30) 作為發電期的 20 年數據
    gen_power_array = field_power_mwh_array[10:30]
    gen_co2_array = field_co2_tons_array[10:30]
    eval_years = len(gen_power_array)

    # 電廠 CAPEX 基於發電期第 1 年的設計容量計算
    design_power_mw = gen_power_array[0] / (8760 * capacity_factor) if eval_years > 0 else 0.0
    
    # 計算各項資本支出 (CAPEX)
    drilling_cost = 27373.64 * 42000
    piping_cost = 4000 * 22500
    plant_cost = design_power_mw * 200000000 
    total_capital_cost = drilling_cost + piping_cost + plant_cost
    
    # 計算各項維運成本 (OPEX)
    well_maint = drilling_cost * 1.5 * 0.01
    plant_maint = plant_cost * 0.015
    hr_cost = 2800000 
    full_annual_opex = well_maint + plant_maint + hr_cost
    
    # 第 0 年僅投入鑽井與管線成本
    initial_capex = drilling_cost + piping_cost
    cumulative_npv = -initial_capex
    npv_array = [cumulative_npv]
    cash_flows_for_irr = [-initial_capex]
    dpp = 999.0
    dpp_found = False
    
    # 逐年計算 30 年的現金流與 NPV
    for year in range(1, years + 1):
        idx = year - 1
        current_power_mwh = field_power_mwh_array[idx]
        current_co2_tons = field_co2_tons_array[idx]
        
        # 計算當年的碳稅成本
        R_cost = current_co2_tons * carbon_price_ntd
        
        if year <= 10:
            # 前 10 年：純封存期 (無發電收入，僅支付井場維護與碳稅)
            revenue = 0.0
            opex = well_maint
            net_cash_flow = revenue - opex - R_cost
            
            # 第 10 年底：投入電廠建置成本
            if year == 10:
                net_cash_flow -= plant_cost
        else:
            # 第 11~30 年：發電期 (賺取電費，支付全額維運與碳稅)
            revenue = current_power_mwh * 1000 * fit_rate_ntd
            opex = full_annual_opex
            net_cash_flow = revenue - opex - R_cost
            
        # 將當年淨現金流折現並累加至 NPV
        discounted_cf = net_cash_flow / ((1 + r) ** year)
        cumulative_npv += discounted_cf
        npv_array.append(cumulative_npv)
        cash_flows_for_irr.append(net_cash_flow)
        
        # 動態尋找折現回收期 (DPP)
        if not dpp_found and cumulative_npv >= 0:
            prev_npv = cumulative_npv - discounted_cf
            if discounted_cf > 0: 
                dpp = (year - 1) + (abs(prev_npv) / discounted_cf)
            else: 
                dpp = float(year)
            dpp_found = True

    # ====================================================
    # LCOE 計算：嚴格對齊 Excel 的靜態年金法 (CRF)
    # 僅針對第 11~30 年的發電期進行均化成本計算
    # ====================================================
    avg_annual_power_kwh = (np.mean(gen_power_array) if eval_years > 0 else 0.0) * 1000.0
    crf = (r * (1 + r)**eval_years) / ((1 + r)**eval_years - 1) if r > 0 else 1.0 / eval_years
    avg_R_cost = np.mean(gen_co2_array) * carbon_price_ntd if eval_years > 0 else 0.0
    
    if avg_annual_power_kwh > 0:
        lcoe = (total_capital_cost * crf + full_annual_opex + avg_R_cost) / avg_annual_power_kwh
    else:
        lcoe = 999.0
        
    # 計算 30 年全生命週期的 IRR
    irr = calculate_stable_irr(cash_flows_for_irr) * 100.0
        
    return npv_array, lcoe, dpp, irr, design_power_mw
