#!/usr/bin/env python3
"""
生成BI实训截图的脚本
使用matplotlib生成类似GWalk风格的图表
"""
import pandas as pd
import matplotlib
# 设置后端和字体（在导入pyplot之前）
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 设置图表风格（先设置风格）
plt.style.use('seaborn-v0_8-whitegrid')

# 设置中文字体 - 在风格之后设置以覆盖默认值
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'Heiti TC', 'Songti SC']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
# 强制重建字体缓存
matplotlib.font_manager._load_fontmanager(try_read_cache=False)

# 数据路径
DATA_DIR = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/实训资源/01-某零售企业经营分析/datasets")
OUTPUT_DIR = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/实训资源/01-某零售企业经营分析/export/files")

def load_data():
    """加载数据"""
    transactions = pd.read_csv(DATA_DIR / "retail_transactions.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    stores = pd.read_csv(DATA_DIR / "stores.csv")

    # 合并数据
    df = transactions.merge(products, on='product_id', how='left')
    df = df.merge(stores, on='store_id', how='left')

    # 计算销售额和毛利
    df['sales'] = df['quantity'] * df['retail_price']
    df['profit'] = df['quantity'] * (df['retail_price'] - df['cost_price'])

    return df, transactions, products, stores

def ss06_city_sales_bar(df):
    """SS-06: 城市销售额柱状图"""
    city_sales = df.groupby('city')['sales'].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262FD']
    bars = ax.bar(city_sales.index, city_sales.values / 10000, color=colors)

    ax.set_xlabel('城市', fontsize=12)
    ax.set_ylabel('销售额 (万元)', fontsize=12)
    ax.set_title('各城市销售额对比', fontsize=14, fontweight='bold')

    # 添加数据标签
    for bar, val in zip(bars, city_sales.values / 10000):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val:.1f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-06_city_sales_bar.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-06 城市销售额柱状图")

def ss07_store_ranking_bar(df):
    """SS-07: 门店销售额排名条形图"""
    store_sales = df.groupby('store_name')['sales'].sum().sort_values(ascending=True).tail(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(store_sales)))
    bars = ax.barh(store_sales.index, store_sales.values / 10000, color=colors)

    ax.set_xlabel('销售额 (万元)', fontsize=12)
    ax.set_ylabel('门店', fontsize=12)
    ax.set_title('门店销售额TOP10排名', fontsize=14, fontweight='bold')

    # 添加数据标签
    for bar, val in zip(bars, store_sales.values / 10000):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}', ha='left', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-07_store_ranking_bar.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-07 门店销售额排名条形图")

def ss08_store_type_comparison(df):
    """SS-08: 门店类型对比"""
    store_type_sales = df.groupby('store_type')['sales'].sum()

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#5B8FF9', '#61DDAA', '#F6BD16']
    bars = ax.bar(store_type_sales.index, store_type_sales.values / 10000, color=colors)

    ax.set_xlabel('门店类型', fontsize=12)
    ax.set_ylabel('销售额 (万元)', fontsize=12)
    ax.set_title('不同门店类型销售额对比', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, store_type_sales.values / 10000):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                f'{val:.1f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-08_store_type_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-08 门店类型对比")

def ss09_size_sales_scatter(df):
    """SS-09: 门店面积与销售额散点图"""
    store_data = df.groupby(['store_name', 'size_sqm'])['sales'].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(store_data['size_sqm'], store_data['sales'] / 10000,
                        c='#5B8FF9', s=100, alpha=0.7, edgecolors='white', linewidth=1)

    ax.set_xlabel('门店面积 (平方米)', fontsize=12)
    ax.set_ylabel('销售额 (万元)', fontsize=12)
    ax.set_title('门店面积与销售额关系', fontsize=14, fontweight='bold')

    # 添加趋势线
    z = np.polyfit(store_data['size_sqm'], store_data['sales'] / 10000, 1)
    p = np.poly1d(z)
    ax.plot(store_data['size_sqm'].sort_values(),
            p(store_data['size_sqm'].sort_values()),
            "r--", alpha=0.8, label='趋势线')
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-09_size_sales_scatter.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-09 门店面积与销售额散点图")

def ss10_category_pie(df):
    """SS-10: 各品类销售额饼图"""
    category_sales = df.groupby('category')['sales'].sum()

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262FD']

    wedges, texts, autotexts = ax.pie(category_sales.values,
                                       labels=category_sales.index,
                                       autopct='%1.1f%%',
                                       colors=colors,
                                       explode=[0.02]*len(category_sales),
                                       shadow=True,
                                       startangle=90)

    ax.set_title('各品类销售额占比', fontsize=14, fontweight='bold')

    # 美化标签
    for text in texts:
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color('white')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-10_category_pie.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-10 各品类销售额饼图")

def ss11_category_margin(df):
    """SS-11: 各品类毛利率对比"""
    category_data = df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum'
    })
    category_data['margin_rate'] = category_data['profit'] / category_data['sales'] * 100
    category_data = category_data.sort_values('margin_rate', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#61DDAA', '#5B8FF9', '#F6BD16', '#65789B', '#7262FD']
    bars = ax.bar(category_data.index, category_data['margin_rate'], color=colors)

    ax.set_xlabel('品类', fontsize=12)
    ax.set_ylabel('毛利率 (%)', fontsize=12)
    ax.set_title('各品类毛利率对比', fontsize=14, fontweight='bold')
    ax.axhline(y=category_data['margin_rate'].mean(), color='red', linestyle='--', label='平均毛利率')
    ax.legend()

    for bar, val in zip(bars, category_data['margin_rate']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-11_category_margin.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-11 各品类毛利率对比")

def ss12_category_quantity(df):
    """SS-12: 品类销量对比"""
    category_qty = df.groupby('category')['quantity'].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262FD']
    bars = ax.bar(category_qty.index, category_qty.values, color=colors)

    ax.set_xlabel('品类', fontsize=12)
    ax.set_ylabel('销量', fontsize=12)
    ax.set_title('各品类销量对比', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, category_qty.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f'{val:,}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-12_category_quantity.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-12 品类销量对比")

def ss14_top10_quantity(df):
    """SS-14: 销量TOP10商品"""
    product_qty = df.groupby('product_name')['quantity'].sum().sort_values(ascending=True).tail(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(product_qty)))
    bars = ax.barh(product_qty.index, product_qty.values, color=colors)

    ax.set_xlabel('销量', fontsize=12)
    ax.set_ylabel('商品', fontsize=12)
    ax.set_title('销量TOP10商品', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, product_qty.values):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'{val:,}', ha='left', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-14_top10_quantity.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-14 销量TOP10商品")

def ss15_top10_sales(df):
    """SS-15: 销售额TOP10商品"""
    product_sales = df.groupby('product_name')['sales'].sum().sort_values(ascending=True).tail(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(product_sales)))
    bars = ax.barh(product_sales.index, product_sales.values / 10000, color=colors)

    ax.set_xlabel('销售额 (万元)', fontsize=12)
    ax.set_ylabel('商品', fontsize=12)
    ax.set_title('销售额TOP10商品', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, product_sales.values / 10000):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}', ha='left', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-15_top10_sales.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-15 销售额TOP10商品")

def ss16_monthly_trend(df):
    """SS-16: 月度销售额趋势图"""
    df['trans_date'] = pd.to_datetime(df['trans_date'])
    df['month'] = df['trans_date'].dt.to_period('M')
    monthly_sales = df.groupby('month')['sales'].sum()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range(len(monthly_sales)), monthly_sales.values / 10000,
            marker='o', linewidth=2, markersize=8, color='#5B8FF9')
    ax.fill_between(range(len(monthly_sales)), monthly_sales.values / 10000,
                    alpha=0.3, color='#5B8FF9')

    ax.set_xticks(range(len(monthly_sales)))
    ax.set_xticklabels([str(m) for m in monthly_sales.index], rotation=45)
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('销售额 (万元)', fontsize=12)
    ax.set_title('2023年月度销售额趋势', fontsize=14, fontweight='bold')

    for i, val in enumerate(monthly_sales.values / 10000):
        ax.text(i, val + 5, f'{val:.0f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-16_monthly_trend.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-16 月度销售额趋势图")

def ss17_quarterly_comparison(df):
    """SS-17: 季度销售对比"""
    df['trans_date'] = pd.to_datetime(df['trans_date'])
    df['quarter'] = df['trans_date'].dt.quarter
    quarterly_sales = df.groupby('quarter')['sales'].sum()

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#5B8FF9', '#61DDAA', '#F6BD16', '#7262FD']
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    bars = ax.bar([quarters[q-1] for q in quarterly_sales.index],
                  quarterly_sales.values / 10000,
                  color=[colors[q-1] for q in quarterly_sales.index])

    ax.set_xlabel('季度', fontsize=12)
    ax.set_ylabel('销售额 (万元)', fontsize=12)
    ax.set_title('2023年各季度销售额对比', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, quarterly_sales.values / 10000):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val:.0f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-17_quarterly_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-17 季度销售对比")

def ss19_member_frequency(df):
    """SS-19: 会员购买频次分布"""
    member_freq = df[df['member_id'].notna()].groupby('member_id').size()
    freq_dist = member_freq.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(freq_dist.index[:8], freq_dist.values[:8], color='#5B8FF9', edgecolor='white')

    ax.set_xlabel('购买次数', fontsize=12)
    ax.set_ylabel('会员数量', fontsize=12)
    ax.set_title('会员购买频次分布', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, freq_dist.values[:8]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'{val:,}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-19_member_frequency.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-19 会员购买频次分布")

def ss20_member_spending(df):
    """SS-20: 会员消费金额分布"""
    member_spending = df[df['member_id'].notna()].groupby('member_id')['sales'].sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(member_spending.values, bins=30, color='#61DDAA', edgecolor='white', alpha=0.8)

    ax.set_xlabel('消费金额 (元)', fontsize=12)
    ax.set_ylabel('会员数量', fontsize=12)
    ax.set_title('会员消费金额分布', fontsize=14, fontweight='bold')

    # 添加均值线
    mean_val = member_spending.mean()
    ax.axvline(x=mean_val, color='red', linestyle='--', label=f'平均: {mean_val:.0f}元')
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-20_member_spending.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-20 会员消费金额分布")

def ss22_member_vs_nonmember(df):
    """SS-22: 会员vs非会员对比"""
    member_sales = df[df['member_id'].notna()]['sales'].sum()
    nonmember_sales = df[df['member_id'].isna()]['sales'].sum()

    fig, ax = plt.subplots(figsize=(8, 8))
    sizes = [member_sales, nonmember_sales]
    labels = ['会员', '非会员']
    colors = ['#5B8FF9', '#F6BD16']

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                       colors=colors, explode=[0.02, 0.02],
                                       shadow=True, startangle=90)

    ax.set_title('会员vs非会员销售额占比', fontsize=14, fontweight='bold')

    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_color('white')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "SS-22_member_vs_nonmember.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ SS-22 会员vs非会员对比")

def main():
    print("=" * 50)
    print("生成BI实训截图")
    print("=" * 50)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 加载数据
    print("\n加载数据...")
    df, transactions, products, stores = load_data()
    print(f"数据加载完成: {len(df):,} 条记录")

    # 生成图表
    print("\n生成图表...")
    ss06_city_sales_bar(df)
    ss07_store_ranking_bar(df)
    ss08_store_type_comparison(df)
    ss09_size_sales_scatter(df)
    ss10_category_pie(df)
    ss11_category_margin(df)
    ss12_category_quantity(df)
    ss14_top10_quantity(df)
    ss15_top10_sales(df)
    ss16_monthly_trend(df)
    ss17_quarterly_comparison(df)
    ss19_member_frequency(df)
    ss20_member_spending(df)
    ss22_member_vs_nonmember(df)

    print("\n" + "=" * 50)
    print("所有图表生成完成!")
    print(f"保存位置: {OUTPUT_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
