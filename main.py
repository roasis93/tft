import streamlit as st
import pandas as pd
import plotly.express as px
from math import comb

st.set_page_config(layout="wide")

# ▼ レベルごとのコスト出現率（%）
COST_DISTRIBUTION = {
    1: {1:100, 2:  0, 3:  0, 4:  0, 5:  0},
    2: {1:100, 2:  0, 3:  0, 4:  0, 5:  0},
    3: {1: 75, 2: 25, 3:  0, 4:  0, 5:  0},
    4: {1: 55, 2: 30, 3: 15, 4:  0, 5:  0},
    5: {1: 45, 2: 33, 3: 20, 4:  2, 5:  0},
    6: {1: 35, 2: 35, 3: 25, 4:  5, 5:  0},
    7: {1: 19, 2: 30, 3: 35, 4: 15, 5:  1},
    8: {1: 15, 2: 25, 3: 35, 4: 20, 5:  5},
    9: {1: 10, 2: 15, 3: 30, 4: 35, 5: 10},
    10:{1:  5, 2: 10, 3: 20, 4: 40, 5: 25},
}

# ▼ コスト帯ごとの1チャンピオンあたりの「枚数」
UNIT_POOL_PER_CHAMPION = {
    1: 30,  # 1コストは 1チャンピオンあたり30枚
    2: 25,  # 2コストは 1チャンピオンあたり25枚
    3: 18,  # 3コストは 1チャンピオンあたり18枚
    4: 10,  # 4コストは 1チャンピオンあたり10枚
    5:  9,  # 5コストは 1チャンピオンあたり9枚
}

# ▼ コスト帯に存在するチャンピオンの「種類数」
CHAMPION_COUNT_PER_COST = {
    1: 14,  # 1コストに14種類
    2: 13,  # 2コストに13種類
    3: 13,  # 3コストに13種類
    4: 12,  # 4コストに12種類
    5:  8,  # 5コストに8種類
}

# ▼ コスト帯の「合計プール枚数」(=1チャンピオンあたり枚数 × 種類数)
UNIT_POOL_SIZE = {
    cost: UNIT_POOL_PER_CHAMPION[cost] * CHAMPION_COUNT_PER_COST[cost]
    for cost in [1, 2, 3, 4, 5]
}
# 例: 1コスト = 30×14=420, 2コスト=25×13=325, ... となる

def calculate_distribution(level, cost, rerolls, purchased_target, purchased_same_cost):
    """
    簡易的に「特定ユニットを何体獲得できるか」の確率分布を計算する。
    - level: プレイヤーレベル (1~10)
    - cost: ユニットコスト (1~5)
    - rerolls: リロール回数
    - purchased_target: 既に購入した「特定ユニット」の枚数
    - purchased_same_cost: 既に購入した「同コスト帯の他ユニット」の枚数
    """
    # 1. レベルごとのコスト出現率 [%]
    cost_prob_percent = COST_DISTRIBUTION.get(level, {}).get(cost, 0)
    cost_prob = cost_prob_percent / 100.0

    # 2. コスト帯 合計プールの残数
    #    = （コスト帯の合計） - （同コストの他ユニットを購入した数）
    #    例えば 1コスト=420枚のうち、すでに 10枚(他ユニット含む)を買っていたら 410残り
    pool_size_total = max(UNIT_POOL_SIZE.get(cost, 0) - purchased_same_cost, 0)

    # 3. 「特定ユニット」自体の残数
    #    = （1チャンピオンあたりの枚数） - （購入済みの対象ユニット）
    #    例: コスト5=1チャンピオンあたり9枚, もう3枚買ってるなら 残6枚
    pool_size_target = max(UNIT_POOL_PER_CHAMPION.get(cost, 0) - purchased_target, 0)

    # プールが枯れている場合 => 0枚しか引けない確率=100%
    if pool_size_total < 1 or pool_size_target < 1:
        return [1.0] + [0.0] * (rerolls * 5)

    # 4. 1枠で特定ユニットを引く確率
    #    = 「コスト帯が出る確率」 × 「同コスト内で特定ユニットを引く割合」
    #    = cost_prob * (pool_size_target / pool_size_total)
    p_single = cost_prob * (pool_size_target / pool_size_total)

    # 5. リロール回数 × 5枠 => total_slots
    total_slots = rerolls * 5

    # 6. 二項分布 (0~total_slots 個まで)
    distribution = []
    for k in range(total_slots + 1):
        p_k = comb(total_slots, k) * (p_single**k) * ((1 - p_single)**(total_slots - k))
        distribution.append(p_k)

    return distribution

def main():
    col_left, col_right = st.columns([1,2])

    with col_left:
        st.title("ユニット確率計算ツール")
        st.write("コスト帯ごとに正確な合計枚数を設定し、**特定ユニットは「1チャンピオンあたりの枚数」で計算** する簡易モデルです。")

        level = st.selectbox("プレイヤーレベル", list(range(1, 11)), index=8)
        cost = st.selectbox("対象ユニットのコスト", [1,2,3,4,5], index=4)
        rerolls = st.number_input("リロール回数", min_value=0, value=20, step=1)

        st.caption("▼ 購入済みによるプール減数(簡易)")
        purchased_target = st.number_input("購入済の対象ユニット数", min_value=0, value=0, step=1)
        purchased_same_cost = st.number_input("購入済の同コスト他ユニット数", min_value=0, value=0, step=1)

        if st.button("計算する"):
            dist = calculate_distribution(level, cost, rerolls, purchased_target, purchased_same_cost)

            df = pd.DataFrame({
                "獲得枚数": range(len(dist)),
                "確率": dist
            })

            # 0〜3体のみ抽出
            df_short = df[df["獲得枚数"] <= 3].copy()

            with col_right:
                st.subheader("結果：獲得枚数の分布 (0〜3体)")
                # 0〜3体のみをグラフ化
                fig = px.bar(
                    df_short,
                    x="獲得枚数",
                    y="確率",
                    color_discrete_sequence=["#f5a623"],
                    labels={"獲得枚数":"対象ユニット枚数","確率":"確率"},
                )
                fig.update_traces(
                    opacity=0.6,
                    hovertemplate="獲得枚数: %{x}体<br>確率: %{y:.2%}"
                )
                fig.update_layout(
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis=dict(
                        linecolor="#ccc",
                        mirror=True,
                        ticks="inside"
                    ),
                    yaxis=dict(
                        linecolor="#ccc",
                        mirror=True,
                        ticks="inside",
                        tickformat=".0%"
                    ),
                    margin=dict(l=50, r=50, t=50, b=50),
                    bargap=0.2,
                )
                st.plotly_chart(fig, use_container_width=True)

                st.write("▼ テーブル (0〜3体)")
                st.table(df_short.style.format({"確率": "{:.2%}"}))

                # もし全範囲の分布も見たい場合は、下記を追加:
                # st.subheader("全範囲")
                # st.dataframe(df.style.format({"確率": "{:.2%}"}))

        else:
            with col_right:
                st.info("左側のパラメータを入力して「計算する」を押してください。")

if __name__ == "__main__":
    main()
