import streamlit as st
import pandas as pd
import numpy as np

# 1. 页面全局配置
st.set_page_config(layout="wide", page_title="Cleanuva | Global Sales & Economic Hub")

# 2. 增强型工业黑金 CSS 样式 (保持 UI 专业感)
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; }
    /* 表格样式：黑底白字 */
    .autohome-table { width: 100%; border-collapse: collapse; background-color: #161b22 !important; border: 1px solid #30363d; margin-top: 10px;}
    .cat-header { background-color: #0d1117 !important; color: #f0ad4e !important; font-weight: bold; text-align: left; padding: 15px 20px !important; border-top: 2px solid #444; font-size: 16px; }
    .autohome-table td { padding: 15px; border: 1px solid #30363d; text-align: center; color: rgba(255,255,255,0.95) !important; font-size: 14px; }
    .param-name { text-align: left !important; background-color: #0d1117; color: #8b949e !important; font-weight: bold; width: 220px; }
    .diff-row { background-color: #1e3a8a44 !important; }
    .model-header td { background-color: #1c2128; font-weight: bold; color: #58a6ff !important; font-size: 18px; border-bottom: 3px solid #58a6ff; }
    
    /* 侧边栏及指标卡片样式 */
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #f0ad4e; margin-bottom: 12px; }
    .sidebar-title { color: #f0ad4e; font-weight: bold; font-size: 1.2rem; margin-bottom: 15px; }
    /* 场景信息主展示框 (Scenario/Region/Date) */
    .constrain-box { background: #0d1117; padding: 12px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px; }
    .constrain-item { font-size: 13px; color: #8b949e; margin-bottom: 4px; }
    .constrain-val { color: #ffffff; font-weight: bold; float: right; }
    
    /* 模块化报价单容器样式 */
    .quote-container { background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); padding: 25px; border-radius: 12px; border: 1px solid #f0ad4e; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# 3. 核心数据加载逻辑 (支持 8 个数据库变量)
@st.cache_data
def load_all_databases():
    try:
        # 加载基础产品参数对比表 (Our vs Competitors)
        xl_prod = pd.ExcelFile("products.xlsx")
        df_our = xl_prod.parse("Our_Products")
        df_comp = xl_prod.parse("Competitors")
        
        # 加载经济 ROI 模型数据
        xl_v1 = pd.ExcelFile("Cleanuva_Economic_Model_v1.xlsx")
        df_sce = xl_v1.parse("Scenarios")
        df_dev = xl_v1.parse("Devices")

        # 加载全球定价、汇率设置及物流规则配置表
        xl_price = pd.ExcelFile("Cleanuva_Price.xlsx")
        df_base = xl_price.parse("Base_Models")
        df_sku = xl_price.parse("SKU_Library")
        # 将 Settings 表设为索引，方便快速提取汇率等参数
        df_settings = xl_price.parse("Settings").set_index('Parameter')
        df_shipping = xl_price.parse("Shipping_Rules")
        
        return df_our, df_comp, df_sce, df_dev, df_base, df_sku, df_settings, df_shipping
    except Exception as e:
        st.error(f"⚠️ System Loading Error: {e}")
        return [None]*8

# 解包 8 个 DataFrame 供全局使用
df_our, df_comp, df_sce, df_dev, df_base, df_sku, df_settings, df_shipping = load_all_databases()

# --- 侧边栏 Logo (白字透明图专用版) ---
with st.sidebar:
    try:
        st.image("logo_w.png", width='stretch')
        st.markdown("<br>", unsafe_allow_html=True)
    except:
        st.sidebar.markdown("<h2 style='color: #f0ad4e;'>CLEANUVA</h2>", unsafe_allow_html=True)

# --- 4. 侧边栏：ROI 经济模型 (保持全英文界面) ---
st.sidebar.markdown("<p class='sidebar-title'>� Economic Model (v1)</p>", unsafe_allow_html=True)

if df_sce is not None and df_dev is not None:
    # 案例选择器
    client_name = st.sidebar.selectbox("� Select Project Case:", options=df_sce['Client/Project'].tolist())
    s = df_sce[df_sce['Client/Project'] == client_name].iloc[0]
    
    # 场景基本信息展示
    st.sidebar.markdown(f"""
    <div class='constrain-box'>
        <div class='constrain-item'>Scenario Mode: <span class='constrain-val'>{s['Scenario']}</span></div>
        <div class='constrain-item'>Region: <span class='constrain-val'>{s['Region']}</span></div>
        <div class='constrain-item'>Analysis Date: <span class='constrain-val'>{str(s['Date'])[:10]}</span></div>
        <div class='constrain-item'>Plant Capacity: <span class='constrain-val'>{s['Plant']} MW</span></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 方案选择逻辑 (增量升级：支持工程师多机型配置方案及单价自定义) ---
    st.sidebar.markdown("### 🛠️ Engineering Fleet Setup", help="Engineer defines the optimal robot mix based on site layout.")
    
    st.sidebar.markdown("### Technical Assumptions")
    # 窗口期悬浮解释 (严格保留原 app_v0.1.py 内容)
    p_window = st.sidebar.number_input("Cleaning Window (Days)", value=int(s['Window']), 
                                       help="The time limit (days) to complete one full cleaning cycle. A shorter window requires more robots to work simultaneously.")
    
    # 班次悬浮解释 (严格保留原 app_v0.1.py 内容)
    p_shifts = st.sidebar.number_input("Shifts per Day", value=int(s['Shifts']), 
                                       help="Number of work shifts per 24 hours. Increasing to 2 shifts (Day+Night) reduces the number of units required.")
    
    # 污损收益悬浮解释 (严格保留原 app_v0.1.py 内容)
    p_soiling = st.sidebar.slider("Soiling Recovery (%)", 0.5, 6.0, float(s['Soiling']), 
                                      help="The expected efficiency gain from automated cleaning compared to infrequent manual cleaning.")

    available_devices = df_dev['Device'].tolist()
    # 升级为多选，支持组合方案
    selected_fleet = st.sidebar.multiselect(
        "Select Fleet Mix:", 
        options=available_devices, 
        default=[available_devices[1]] if len(available_devices) > 1 else [available_devices[0]],
        help="Engineering step: Choose one or multiple robot models based on terrain (e.g., NuvaSpan for ground + NuvaTrack for trackers)."
    )

    # 变量初始化
    total_fleet_cycle_cap = 0
    total_initial_capex = 0
    total_annual_robot_opex = 0

    # 动态渲染每种选定设备的配置项
    for robot_name in selected_fleet:
        d_spec = df_dev[df_dev['Device'] == robot_name].iloc[0]
        with st.sidebar.expander(f"⚙️ {robot_name} Config", expanded=True):
            # 支持手动修改单价 (考虑折扣或实际采购价)
            custom_unit_price = st.number_input(
                f"Unit Price ($) - {robot_name}", 
                value=float(d_spec['Unit price']),
                key=f"custom_p_{robot_name}",
                help="Actual quoted price. Adjust this if there are bulk discounts or extra hardware costs."
            )
            
            # 计算建议数量 (按比例分配产能)
            target_share = s['Plant'] / len(selected_fleet)
            suggested_q = int(np.ceil((target_share / p_window) / (d_spec['Capacity'] * p_shifts) * s.get('Redundancy', 1.1)))
            
            q_fleet = st.number_input(
                f"Units Count - {robot_name}", 
                min_value=0, value=suggested_q, 
                key=f"custom_q_{robot_name}",
                help="Adjust based on suggested minimum units to ensure project deadline is met."
            )

            # 汇总计算 (周期产能、投入总额、运维支出)
            total_fleet_cycle_cap += q_fleet * d_spec['Capacity'] * p_shifts * p_window
            total_initial_capex += q_fleet * custom_unit_price
            total_annual_robot_opex += (d_spec.get('Consumable', 500) * s['Freq'] + d_spec.get('Warranty', 390)) * q_fleet

    # 产能达标看板 (Engineering Adequacy Check)
    is_adequate = total_fleet_cycle_cap >= s['Plant']
    status_color = "#58a6ff" if is_adequate else "#ff4b4b"
    st.sidebar.markdown(f"""
    <div style='border:1px solid {status_color}; padding:10px; border-radius:5px; margin-bottom:15px; background:rgba(0,0,0,0.2);'>
        <p style='color:#8b949e; font-size:11px; margin:0;'>FLEET CAPACITY CHECK</p>
        <p style='color:{status_color}; font-size:16px; font-weight:bold; margin:0;'>{total_fleet_cycle_cap:.1f} MW / cycle</p>
        <p style='color:#666; font-size:10px; margin:0;'>Target: {s['Plant']} MW | Adequacy: {'YES' if is_adequate else 'NO (Add Units)'}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 收益模型计算 (逻辑更新：Total Benefit = Savings + Extra Revenue) ---
    total_capex = total_initial_capex
    annual_manual_saving = (s['Plant'] * s['Manual'] * s['Freq']) - total_annual_robot_opex
    
    # 发电增收计算公式：MW * 1000 * 8760h * 容量系数 * 提升率 * 电价
    annual_gen_gain = (s['Plant'] * 1000 * 8760 * (s.get('CapFactor', 17)/100)) * (p_soiling/100) * s['ElecPrice']
    
    net_benefit = annual_manual_saving + annual_gen_gain
    # 回本年限：采用你定义的累计收益覆盖 CAPEX 逻辑
    payback_yrs = total_capex / net_benefit if net_benefit > 0 else 99

    # --- 测算结果指标展示 (修复 NameError: 移除 suggested_qty 引用) ---
    st.sidebar.markdown(f"""
    <div class='metric-card'>
        <p style='color:#8b949e; font-size:11px; margin:0;'>TOTAL INVESTMENT (CAPEX)</p>
        <h3 style='color:#ffffff; margin:0;'>$ {total_initial_capex:,.0f}</h3>
        <p style='color:#58a6ff; font-size:12px; margin:0;'>Fleet Configuration Applied</p>
    </div>
    <div class='metric-card'>
        <p style='color:#8b949e; font-size:11px; margin:0;'>PAYBACK PERIOD</p>
        <h3 style='color:#f0ad4e; margin:0;'>{payback_yrs:.2f} Years</h3>
        <p style='color:#8b949e; font-size:10px; margin:0;'>Based on Saving + Generation Gain</p>
    </div>
    """, unsafe_allow_html=True)

    # --- [增量] 侧边栏：5 年长期效益指标 (对齐 Yearly 表逻辑) ---
    total_5y_benefit = net_benefit * 5
    roi_5y = (total_5y_benefit / total_initial_capex * 100) if total_initial_capex > 0 else 0
    
    st.sidebar.markdown(f"""
    <div class='metric-card'>
        <p style='color:#8b949e; font-size:11px; margin:0;'>5-YEAR PROJECTED PROFIT</p>
        <h3 style='color:#58a6ff; margin:0;'>$ {total_5y_benefit:,.0f}</h3>
        <p style='color:#8b949e; font-size:10px; margin:0;'>Cumulative ROI (5Y): {roi_5y:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. 主界面：多维工作区 (严格保留所有对比逻辑) ---
# 创建三个 Tab，分别对应：参数对比、报价生成、效益分析
tab_compare, tab_quote, tab_roi = st.tabs([
    "📊 Product Battlecards", 
    "📜 Quotation Builder", 
    "📈 Financial Outlook"
])

# --- 5. 主界面：产品参数对比 (完全保留原有功能) ---
import base64

# --- 辅助函数：将本地图片转为网页可显示的 Base64 编码 ---
def get_image_base64(path):
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    except:
        return None

with tab_compare:
    # --- 5. 主界面：产品参数对比 (带机器人渲染图版) ---
    st.title("☀️ Cleanuva | Global Product Hub")

    if df_our is not None:
        show_comp = st.checkbox("Show Competitor Battlecards (Internal Only)", value=False)
        all_models = df_our['Model'].unique().tolist()
        if show_comp and df_comp is not None:
            all_models += df_comp['Model'].unique().tolist()
        
        selected = st.multiselect("Models to Display:", options=all_models, default=all_models[:2])

        if selected:
            full_df = pd.concat([df_our, df_comp]) if df_comp is not None else df_our
            compare_df = full_df[full_df['Model'].isin(selected)]
            
            # 建立数据透视表
            pivot_df = compare_df.pivot_table(
                index=['Primary Category', 'Secondary Parameter'], 
                columns='Model', 
                values='Value', 
                aggfunc='first'
            ).reset_index()

            # --- 开始构建带图片的 HTML 表格 ---
            html = "<table class='autohome-table'>"
            
            # 第一行：显示机器人渲染图
            html += "<tr style='background-color: #1c2128;'><td class='param-name'>Product Render</td>"
            for m in selected:
                # 自动寻找对应的图片，例如 NuvaSpan.png
                img_file = f"{m.replace(' ', '_')}.png" 
                img_base64 = get_image_base64(img_file)
                if img_base64:
                    html += f"<td><img src='{img_base64}' style='width:180px; border-radius:8px; margin:10px;'></td>"
                else:
                    html += "<td><div style='height:120px; display:flex; align-items:center; justify-content:center; color:#444; font-size:12px;'>Image not found<br>({img_file})</div></td>"
            html += "</tr>"

            # 第二行：显示型号名称
            html += "<tr class='model-header'><td class='param-name'>Model Name</td>"
            for m in selected:
                html += f"<td>{m}</td>"
            html += "</tr>"

            # 后续数据行
            current_cat = ""
            for _, row in pivot_df.iterrows():
                # 插入分类标题行 (如 Technical, Power 等)
                if str(row['Primary Category']) != current_cat:
                    current_cat = str(row['Primary Category'])
                    html += f"<tr><td colspan='{len(selected)+1}' class='cat-header'>■ {current_cat}</td></tr>"
                
                # 检查参数是否一致，不一致则高亮 (diff-row)
                vals = [str(row[m]) for m in selected]
                row_class = "diff-row" if len(set(vals)) > 1 and len(selected) > 1 else ""
                
                html += f"<tr class='{row_class}'><td class='param-name'>{row['Secondary Parameter']}</td>"
                for m in selected:
                    val = row[m]
                    html += f"<td>{val if str(val) != 'nan' else '--'}</td>"
                html += "</tr>"
                
            html += "</table>"
            
            # 在 Streamlit 中渲染 HTML
            st.markdown(html, unsafe_allow_html=True)

with tab_quote:
    # --- 6. 全球报价配置系统 (Global Quotation Builder) ---
    if df_base is not None and df_settings is not None:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #f0ad4e;'>� Global Configuration & Quotation Hub</h2>", unsafe_allow_html=True)
        
        # 【修复点 1】在这里初始化变量，防止后面 PDF 函数找不到它
        user_selections = []

        # 获取 Excel 中定义的汇率参数 (EUR 对 USD)
        eur_to_usd = float(df_settings.loc['EUR_to_USD', 'Value'])
        
        # 报价基础配置栏
        col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 2])
        with col_cfg1:
            # 货币切换逻辑
            currency = st.radio("Currency Selection", ["EUR (€)", "USD ($)"], horizontal=True)
            rate = 1.0 if "EUR" in currency else eur_to_usd
            sym = "€" if "EUR" in currency else "$"
        
        with col_cfg2:
            # 物流及交货地点选择逻辑
            dest_region = st.selectbox("Destination Region", df_shipping['Region'].unique())
            methods = df_shipping[df_shipping['Region'] == dest_region]
            ship_method = st.selectbox("Shipping Mode", methods['Delivery_Method'].tolist())
            # 从 Excel 获取对应的欧元运费成本
            ship_cost_base = methods[methods['Delivery_Method'] == ship_method]['Cost_EUR'].values[0]

        # --- IMPORTANT FIX: Define 'm_info' BEFORE using it in columns ---
        # 【核心修复】：在进入 columns 之前就定义好选中的型号数据
        sel_model = st.selectbox("Core Robot Platform", df_base['Model_Name'].tolist(), key="main_model_select")
        m_info = df_base[df_base['Model_Name'] == sel_model].iloc[0]
        # -----------------------------------------------------------

        with st.container():
            c_left, c_right = st.columns([1, 2])
            
            with c_left:
                # 第一步：选择整机型号
                st.markdown("#### 1. System Selection")
                sel_model = st.selectbox("Core Robot Platform", df_base['Model_Name'].tolist())
                m_data = df_base[df_base['Model_Name'] == sel_model].iloc[0]
                
                # 计算并显示换算后的整机基础价
                base_p_conv = m_data['Price_EUR'] * rate
                st.metric("Base Platform Price", f"{sym} {base_p_conv:,.0f}")
                
                # 动态展示该型号基础包包含的硬件 (来自 Excel 列 Standard_Includes)
                st.markdown("##### � Standard Inclusion:")
                for item in str(m_data['Standard_Includes']).split(','):
                    st.markdown(f"- {item.strip()}")
                st.caption(f"Warranty: {m_data['Warranty_Base']}")

            with c_right:
                st.markdown("#### 2. Options & Logistics")
                # 过滤可选配件
                valid_skus = df_sku[(df_sku['Applicable_To'] == 'ALL') | (df_sku['Applicable_To'].str.contains(m_info['Model_ID']))]
                
                # 初始化选件总价
                opt_total = 0

                # 遍历并显示每个选配件
                for _, row in valid_skus.iterrows():
                    # 换算当前选件的单价
                    p_opt_conv = row['Price_EUR'] * rate
                    
                    # --- 关键修复：创建列变量 ---
                    col_n, col_p, col_q = st.columns([3, 1.5, 1])
                    
                    with col_n:
                        st.write(f"**{row['Item_Name']}**")
                    with col_p:
                        st.write(f"{sym} {p_opt_conv:,.0f}")
                    with col_q:
                        # 获取用户输入的数量
                        qty = st.number_input("Qty", min_value=0, step=1, key=f"sku_input_{row['SKU_ID']}")
                    
                    # 如果数量大于 0，累加到总价并记录到 PDF 清单
                    if qty > 0:
                        opt_total += (p_opt_conv * qty)
                        user_selections.append({
                            "name": row['Item_Name'], 
                            "price": p_opt_conv, 
                            "qty": qty
                        })
                
                # 计算并展示运费 (自动根据目的地换算)
                ship_total = ship_cost_base * rate
                st.markdown(f"**Logistics Charge ({ship_method}):** {sym} {ship_total:,.0f}")

        # 计算最终总计
        grand_total = base_p_conv + opt_total + ship_total

        # 最终报价汇总卡片 (如果免运费显示蓝色边框，否则显示金黄色边框)
        st.markdown(f"""
        <div class='quote-container' style="border-left: 10px solid {'#58a6ff' if ship_total == 0 else '#f0ad4e'};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="color: #8b949e; margin:0;">GLOBAL SALES QUOTE: {sel_model}</h4>
                    <p style="color: #58a6ff; font-size: 13px; margin:0;">Destination: {dest_region} | Incoterms: {ship_method}</p>
                </div>
                <div style="text-align: right;">
                    <p style="color: #8b949e; font-size: 12px; margin:0;">ESTIMATED TOTAL ({currency})</p>
                    <h1 style="color: #ffffff; margin:0;">{sym} {grand_total:,.2f}</h1>
                    <p style="color: #666; font-size: 11px;">* Excl. Local Import Duties. Exchange Rate: 1 EUR = {eur_to_usd} USD</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 同步 Excel 按钮逻辑
    if st.sidebar.button("� Sync with Excel"):
        st.cache_data.clear()
        st.rerun()

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import io

    # --- 7. PDF 生成函数 (修复重叠与 Logo 显示问题) ---
    def generate_pdf_quote(model_name, inclusions, selected_skus, ship_method, ship_cost, total_price, currency_sym):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # --- 绘制页眉背景 ---
        p.setFillColor(colors.HexColor("#161b22"))
        p.rect(0, height - 1.5*inch, width, 1.5*inch, fill=1)
        
        # --- 修复 1：调整 Logo 绘制顺序和位置 ---
        # 先画背景再画 Logo，确保 Logo 在最上层
        try:
            # 调整了 Y 坐标，确保在 1.5inch 的页眉区域内居中
            p.drawImage("logo_b.png", 0.5*inch, height - 1.1*inch, width=1.5*inch, preserveAspectRatio=True, mask='auto')
        except:
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 24)
            p.drawString(0.5*inch, height - 0.8*inch, "CLEANUVA")
        
        # 页眉文字
        p.setFillColor(colors.white)
        p.setFont("Helvetica", 10)
        p.drawRightString(width - 0.5*inch, height - 0.8*inch, "OFFICIAL SALES QUOTATION")
        p.drawRightString(width - 0.5*inch, height - 1.0*inch, f"REF: {pd.Timestamp.now().strftime('%Y%m%d%H%M')}")
        
        # --- 基础信息区域 ---
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(0.5*inch, height - 2*inch, f"Product Model: {model_name}")
        p.setFont("Helvetica", 10)
        p.drawString(0.5*inch, height - 2.2*inch, f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
        p.drawString(0.5*inch, height - 2.4*inch, f"Shipping Terms: {ship_method}")

        # 1. Standard inclusions
        p.setFont("Helvetica-Bold", 12)
        p.drawString(0.5*inch, height - 3*inch, "1. Standard Package Includes:")
        p.setFont("Helvetica", 10)
        y_pos = height - 3.2*inch
        for item in inclusions.split(','):
            p.drawString(0.7*inch, y_pos, f"- {item.strip()}")
            y_pos -= 0.15*inch

        # 2. Options 表头
        y_pos -= 0.4*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(0.5*inch, y_pos, "2. Custom Options & Logistics:")
        
        y_pos -= 0.3*inch
        p.setFont("Helvetica-Bold", 10)
        p.drawString(0.7*inch, y_pos, "Item Description")
        p.drawString(4*inch, y_pos, "Qty")
        p.drawString(5*inch, y_pos, "Subtotal")
        p.line(0.5*inch, y_pos - 0.05*inch, 5.5*inch, y_pos - 0.05*inch)

        # --- 修复 2：动态计算 Y 轴位置，防止重叠 ---
        p.setFont("Helvetica", 10)
        y_pos -= 0.2*inch
        for item in selected_skus:
            # 如果项目太多快到底部了，简单处理：这里可以加分页逻辑，或者缩小间距
            p.drawString(0.7*inch, y_pos, item['name'])
            p.drawString(4.1*inch, y_pos, str(item['qty']))
            p.drawString(5*inch, y_pos, f"{currency_sym} {item['price']*item['qty']:,.2f}")
            y_pos -= 0.2*inch

        # 打印运费
        p.drawString(0.7*inch, y_pos, f"Logistics Charge ({ship_method})")
        p.drawString(4.1*inch, y_pos, "1")
        p.drawString(5*inch, y_pos, f"{currency_sym} {ship_cost:,.2f}")

        # --- 修复核心：无论上面有多少项，总价框都跟在最后一项后面，而不是固定死位置 ---
        # 我们给 y_pos 下移一段距离再画总价框
        y_pos -= 0.6*inch 
        
        # 如果 y_pos 太低（比如小于 1.5 inch），PDF 可能会画到纸外面
        # 正常配件量不会遇到，这里我们预留足够空间
        p.setStrokeColor(colors.HexColor("#f0ad4e"))
        p.setLineWidth(1)
        p.roundRect(3.5*inch, y_pos, 2*inch, 0.4*inch, 5, stroke=1, fill=0)
        
        p.setFont("Helvetica-Bold", 11)
        # 调整文字在框内居中显示
        p.drawString(3.6*inch, y_pos + 0.15*inch, "GRAND TOTAL:")
        p.drawRightString(5.4*inch, y_pos + 0.15*inch, f"{currency_sym} {total_price:,.2f}")

        # 页脚
        p.setFont("Helvetica-Oblique", 8)
        p.setFillColor(colors.gray)
        footer_text = "* Valid for 30 days. All prices exclude local import duties and taxes."
        p.drawCentredString(width/2, 0.5*inch, footer_text)

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

    # --- 8. 显示下载 PDF 按钮 (PDF Download Section) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_pdf, _ = st.columns([1, 3])

    with col_pdf:
        # 检查总价是否大于 0 且变量已定义
        if 'grand_total' in locals() and grand_total > 0:
            pdf_data = generate_pdf_quote(
                sel_model, 
                str(m_data['Standard_Includes']), 
                user_selections, 
                ship_method, 
                ship_total, 
                grand_total, 
                sym
            )
            
            st.download_button(
                label="� Download Official Quote (PDF)",
                data=pdf_data,
                file_name=f"Cleanuva_Quote_{sel_model}_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width='stretch'  # 这里也要改
            )

# [增量] 5年财务展望分析
with tab_roi:
    st.markdown("### 📈 5-Year Financial & ROI Analysis")
    if 'total_initial_capex' in locals() and total_initial_capex > 0:
        # 抓取 Yearly 表逻辑：计算 5 年累计现金流
        chart_years = ["Year 0 (Inv.)", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
        cumulative_cash_flow = [-total_initial_capex]
        for year in range(1, 6):
            # 累计值 = (年度收益 * 年份) - 初始投入
            cumulative_cash_flow.append((net_benefit * year) - total_initial_capex)
        
        roi_df = pd.DataFrame({"Timeline": chart_years, "Net Cash Flow ($)": cumulative_cash_flow})
        
        # 绘制回本曲线图
        st.area_chart(roi_df.set_index("Timeline"), width='stretch')
        
        # --- [增量] 增加：发电损失挽回分析 (针对不清洗客户的止损逻辑) ---
        st.markdown("<br><h3 style='color: #58a6ff;'>💎 Revenue Recovery Analysis</h3>", unsafe_allow_html=True)
        
        # 逻辑：即使之前不清洗（人工费为0），如果不洗，每年丢掉的电费（annual_gen_gain）也是巨大的
        recovery_data = pd.DataFrame({
            'Year': [f"Year {i}" for i in range(1, 6)],
            'Potential Revenue Loss (No Clean)': [annual_gen_gain] * 5,
            'Robot Operation Cost': [total_annual_robot_opex] * 5
        }).set_index('Year')

        # 使用堆叠柱状图，直观展示“损失”与“投入”的悬殊比例
        st.bar_chart(recovery_data, width='stretch')
        
        st.info(f"💡 **The Cost of Doing Nothing:** By not cleaning, you are effectively losing **${annual_gen_gain:,.0f}** in potential revenue every year. "
                f"The robotic solution recovers this massive loss with an annual maintenance cost of only **${total_annual_robot_opex:,.0f}**.")
        
        # 显示回本结论
        st.success(f"💰 Projected Breakeven Point: **{payback_yrs:.2f}** years.")
        st.info("📊 Logic: This forecast includes both Manual Savings and Extra Generation Gains.")
    else:
        st.warning("Please configure your Fleet Setup in the sidebar to view the financial projection.")