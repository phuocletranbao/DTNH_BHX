import streamlit as st
import pandas as pd
from datetime import datetime

# ===== 1. Đọc file =====
file_now  = "data.xlsx"   # dữ liệu tháng hiện tại (không có cột Ngày)
file_old  = "data3.xlsx"  # dữ liệu tổng 3 tháng trước
file_nh   = "WEB/nh.xlsx"     # mapping ngành hàng -> nhóm

df_now = pd.read_excel(file_now)
df_old = pd.read_excel(file_old)
mapping = pd.read_excel(file_nh)

# ===== 2. Chuẩn hóa =====
df_now.columns = df_now.columns.str.strip()
df_old.columns = df_old.columns.str.strip()
mapping.columns = mapping.columns.str.strip()

# Merge nhóm ngành
df_now = df_now.merge(mapping, on="Ngành hàng", how="left")
df_old = df_old.merge(mapping, on="Ngành hàng", how="left")

# ===== 3. Hàm tính toán tổng quan =====
def tinh_tong_quan(data):
    tong_sl = data["Tổng số lượng"].sum()
    tong_dt = data["Tổng doanh thu"].sum()
    nhom = data.groupby("Nhóm")["Tổng doanh thu"].sum().to_dict()
    return tong_sl, tong_dt, nhom.get("FRESH",0), nhom.get("FMCG",0), nhom.get("ĐÔNG MÁT",0)

def calc_change(new, old):
    if old == 0:
        return 0 if new == 0 else 100
    return (new - old) / old * 100

def style_change(val):
    if val < 0:
        return f"<span style='color:red'>{val:.2f}%</span>"
    elif val > 5:
        return f"<span style='color:green'>{val:.2f}%</span>"
    else:
        return f"{val:.2f}%"

# ===== 4. Xác định ngày hiện tại =====
today = datetime.now().day - 1
if today <= 0:
    st.warning("⚠️ Chưa đủ dữ liệu trong tháng này để ước tính (vì mới là ngày 1).")
    st.stop()
so_ngay_trong_thang = 31  # hoặc 30 nếu muốn cố định

# ===== 🌍 Tổng Quan KV Bảo Phước =====
st.title("📊 Tổng Quan KV Bảo Phước")

# Ước tính toàn hệ thống
tong_doanh_thu_ht = df_now["Tổng doanh thu"].sum()
tong_so_luong_ht = df_now["Tổng số lượng"].sum()

du_kien_ht = tong_doanh_thu_ht / today * so_ngay_trong_thang
tile_du_kien_ht = du_kien_ht / tong_doanh_thu_ht

df_now_all_du_kien = df_now.copy()
df_now_all_du_kien["Tổng doanh thu"] *= tile_du_kien_ht
if "Tổng số lượng" in df_now_all_du_kien.columns:
    df_now_all_du_kien["Tổng số lượng"] *= tile_du_kien_ht

# Tính tổng quan
now_sl_all, now_dt_all, now_fresh_all, now_fmcg_all, now_dm_all = tinh_tong_quan(df_now_all_du_kien)
old_sl_all, old_dt_all, old_fresh_all, old_fmcg_all, old_dm_all = tinh_tong_quan(df_old)

# Trung bình 3 tháng
old_sl_all /= 3; old_dt_all /= 3; old_fresh_all /= 3; old_fmcg_all /= 3; old_dm_all /= 3

# Hiển thị kết quả
st.info(f"📅 Ước tính đến ngày {today}/10 ({today} ngày đầu tháng, dự kiến {so_ngay_trong_thang} ngày).")
st.markdown("### 🔹 So sánh Trung bình 3 tháng trước với Dự kiến tháng này (Toàn KV)")

tong_quan_all = {
    "Tổng Số lượng Dự kiến": (now_sl_all, calc_change(now_sl_all, old_sl_all)),
    "Tổng Doanh thu Dự kiến": (now_dt_all, calc_change(now_dt_all, old_dt_all)),
    "Doanh thu FRESH": (now_fresh_all, calc_change(now_fresh_all, old_fresh_all)),
    "Doanh thu FMCG": (now_fmcg_all, calc_change(now_fmcg_all, old_fmcg_all)),
    "Doanh thu ĐÔNG MÁT": (now_dm_all, calc_change(now_dm_all, old_dm_all)),
}

for k, (v, c) in tong_quan_all.items():
    st.markdown(f"**{k}:** {int(v):,} (% So với TB 3 tháng: {style_change(c)})", unsafe_allow_html=True)

st.markdown("---")

# ===== 5. Chọn siêu thị =====
list_sieuthi = df_now["Mã siêu thị"].unique()
chon_sieuthi = st.selectbox("Chọn siêu thị", list_sieuthi)

df_now = df_now[df_now["Mã siêu thị"] == chon_sieuthi]
df_old = df_old[df_old["Mã siêu thị"] == chon_sieuthi]

# ===== 6. Ước tính doanh thu & số lượng tháng này dựa trên số ngày hiện tại - 1 =====
tong_doanh_thu_hien_tai = df_now["Tổng doanh thu"].sum()
tong_so_luong_hien_tai = df_now["Tổng số lượng"].sum()

du_kien_thang = tong_doanh_thu_hien_tai / today * so_ngay_trong_thang
tile_du_kien = du_kien_thang / tong_doanh_thu_hien_tai

df_now_du_kien = df_now.copy()
df_now_du_kien["Tổng doanh thu"] = df_now_du_kien["Tổng doanh thu"] * tile_du_kien
if "Tổng số lượng" in df_now_du_kien.columns:
    df_now_du_kien["Tổng số lượng"] = df_now_du_kien["Tổng số lượng"] * tile_du_kien

# ===== 7. Hiển thị chỉ số tổng quan (theo siêu thị chọn) =====
st.title("🏬 Báo cáo Dự kiến theo Siêu thị")
st.subheader(f"Siêu thị: {chon_sieuthi}")
st.info(f"📅 Ước tính đến ngày {today}/10 ({today} ngày đầu tháng, dự kiến {so_ngay_trong_thang} ngày).")

st.markdown(f"### 🔹 So sánh Trung bình 3 tháng trước với Dự kiến tháng này")

now_sl, now_dt, now_fresh, now_fmcg, now_dm = tinh_tong_quan(df_now_du_kien)
old_sl, old_dt, old_fresh, old_fmcg, old_dm = tinh_tong_quan(df_old)
old_sl /= 3; old_dt /= 3; old_fresh /= 3; old_fmcg /= 3; old_dm /= 3

tong_quan = {
    "Tổng Số lượng Dự kiến": (now_sl, calc_change(now_sl, old_sl)),
    "Tổng Doanh thu Dự kiến": (now_dt, calc_change(now_dt, old_dt)),
    "Doanh thu FRESH": (now_fresh, calc_change(now_fresh, old_fresh)),
    "Doanh thu FMCG": (now_fmcg, calc_change(now_fmcg, old_fmcg)),
    "Doanh thu ĐÔNG MÁT": (now_dm, calc_change(now_dm, old_dm)),
}

for k, (v, c) in tong_quan.items():
    st.markdown(f"**{k}:** {int(v):,} (% So với TB 3 tháng: {style_change(c)})", unsafe_allow_html=True)

# ===== 8. Doanh thu theo Ngành hàng (theo Nhóm) =====
st.markdown("### 🔹 Doanh thu theo Ngành hàng (theo Nhóm)")

nh_now = df_now_du_kien.groupby(["Nhóm","Ngành hàng"], as_index=False).agg({
    "Tổng số lượng":"sum",
    "Tổng doanh thu":"sum"
})

nh_old = df_old.groupby(["Nhóm","Ngành hàng"], as_index=False).agg({
    "Tổng số lượng":"sum",
    "Tổng doanh thu":"sum"
})
nh_old["Tổng số lượng"] /= 3
nh_old["Tổng doanh thu"] /= 3

nh_merge = nh_now.merge(
    nh_old,
    on=["Nhóm","Ngành hàng"],
    how="left",
    suffixes=("","_old")
).fillna(0)

nh_merge = nh_merge[nh_merge["Nhóm"].isin(["FRESH","FMCG","ĐÔNG MÁT"])]

nh_merge["% TB 3 Tháng"] = nh_merge.apply(
    lambda r: calc_change(r["Tổng doanh thu"], r["Tổng doanh thu_old"]),
    axis=1
)

nh_merge["Tổng số lượng"] = nh_merge["Tổng số lượng"].astype(int).map("{:,}".format)
nh_merge["Tổng doanh thu"] = nh_merge["Tổng doanh thu"].astype(int).map("{:,}".format)
nh_merge["% TB 3 Tháng"] = nh_merge["% TB 3 Tháng"].apply(lambda x: style_change(x))
nh_merge = nh_merge.sort_values(["Nhóm","Tổng doanh thu"], ascending=[True, False])

st.write(
    nh_merge[["Nhóm","Ngành hàng","Tổng số lượng","Tổng doanh thu","% TB 3 Tháng"]]
    .to_html(escape=False,index=False),
    unsafe_allow_html=True
)

# ===== 9. Top 5 model theo 5 ngành hàng doanh thu cao nhất =====
st.markdown("### 🔹 Top 5 Model theo 5 Ngành hàng Doanh thu cao nhất (Dự kiến)")

top5_nganh = (
    df_now_du_kien.groupby("Ngành hàng")["Tổng doanh thu"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index
)

for nganh in top5_nganh:
    df_n = df_now_du_kien[df_now_du_kien["Ngành hàng"] == nganh]
    df_o = df_old[df_old["Ngành hàng"] == nganh]

    if df_n.empty:
        continue

    top_now = df_n.groupby("Model", as_index=False).agg({
        "Tổng số lượng": "sum",
        "Tổng doanh thu": "sum"
    }).sort_values("Tổng doanh thu", ascending=False).head(5)

    top_old = df_o.groupby("Model", as_index=False).agg({"Tổng doanh thu": "sum"})
    top_old["Tổng doanh thu"] = top_old["Tổng doanh thu"] / 3

    top_merge = top_now.merge(
        top_old, on="Model", how="left", suffixes=("", "_old")
    ).fillna(0)
    top_merge["% TB 3 Tháng"] = top_merge.apply(
        lambda r: calc_change(r["Tổng doanh thu"], r["Tổng doanh thu_old"]), axis=1
    )

    top_merge["Tổng số lượng"] = top_merge["Tổng số lượng"].astype(int).map("{:,}".format)
    top_merge["Tổng doanh thu"] = top_merge["Tổng doanh thu"].astype(int).map("{:,}".format)
    top_merge["% TB 3 Tháng"] = top_merge["% TB 3 Tháng"].apply(lambda x: style_change(x))

    st.markdown(f"#### 🏷️ {nganh}")
    st.write(
        top_merge[["Model", "Tổng số lượng", "Tổng doanh thu", "% TB 3 Tháng"]]
        .to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
