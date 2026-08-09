import numpy as np

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

def calculate_economics(carbon_price_ntd: float, fit_rate_ntd: float, discount_rate: float, power_mwh_array: list, co2_tons_array: list, capacity_factor: float):
    years = 30 # 專案總長度 30 年
    r = discount_rate
    
    field_power_mwh_array = np.array(power_mwh_array)
    field_co2_tons_array = np.array(co2_tons_array)

    # 電廠 CAPEX 基於第 11 年（索引 10）的設計容量計算
    design_power_mw = field_power_mwh_array[10] / (8760 * capacity_factor) if len(field_power_mwh_array) > 10 else 0.0
    
    drilling_cost = 27373.64 * 42000
    piping_cost = 4000 * 22500
    plant_cost = design_power_mw * 200000000 
    total_capital_cost = drilling_cost + piping_cost + plant_cost
    
    well_maint = drilling_cost * 1.5 * 0.01
    plant_maint = plant_cost * 0.015
    hr_cost = 2800000 
    full_annual_opex = well_maint + plant_maint + hr_cost
    
    # ====================================================
    # 【修正】繪製完整的 30 年 NPV 現金流
    # ====================================================
    initial_capex = drilling_cost + piping_cost # 第 0 年只打井
    cumulative_npv = -initial_capex
    npv_array = [cumulative_npv]
    cash_flows_for_irr = [-initial_capex]
    dpp = 999.0
    dpp_found = False
    
    for year in range(1, years + 1):
        idx = year - 1
        current_power_mwh = field_power_mwh_array[idx]
        current_co2_tons = field_co2_tons_array[idx]
        
        R_cost = current_co2_tons * carbon_price_ntd
        
        if year <= 10:
            # 前 10 年：純封存期 (無收入，付井場維護與碳稅)
            revenue = 0.0
            opex = well_maint
            net_cash_flow = revenue - opex - R_cost
            
            # 第 10 年底：砸錢蓋發電廠
            if year == 10:
                net_cash_flow -= plant_cost
        else:
            # 第 11~30 年：發電期 (有收入，付全額維運與碳稅)
            revenue = current_power_mwh * 1000 * fit_rate_ntd
            opex = full_annual_opex
            net_cash_flow = revenue - opex - R_cost
            
        discounted_cf = net_cash_flow / ((1 + r) ** year)
        cumulative_npv += discounted_cf
        npv_array.append(cumulative_npv)
        cash_flows_for_irr.append(net_cash_flow)
        
        if not dpp_found and cumulative_npv >= 0:
            prev_npv = cumulative_npv - discounted_cf
            if discounted_cf > 0: dpp = (year - 1) + (abs(prev_npv) / discounted_cf)
            else: dpp = float(year)
            dpp_found = True

    # LCOE 依然只算後 20 年的發電期
    n_gen = 20 
    gen_power_array = field_power_mwh_array[10:30]
    avg_annual_power_kwh = (np.mean(gen_power_array) if len(gen_power_array) > 0 else 0.0) * 1000.0
    crf = (r * (1 + r)**n_gen) / ((1 + r)**n_gen - 1) if r > 0 else 1.0 / n_gen
    avg_R_cost = np.mean(field_co2_tons_array[10:30]) * carbon_price_ntd if len(field_co2_tons_array[10:30]) > 0 else 0.0
    
    if avg_annual_power_kwh > 0:
        lcoe = (total_capital_cost * crf + full_annual_opex + avg_R_cost) / avg_annual_power_kwh
    else:
        lcoe = 999.0
        
    irr = calculate_stable_irr(cash_flows_for_irr) * 100.0
        
    return npv_array, lcoe, dpp, irr