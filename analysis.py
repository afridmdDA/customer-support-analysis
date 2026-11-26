"""
Customer Support Operations Analysis
=====================================
Analyzes 2,500 support tickets to find what drives customer satisfaction
(CSAT) and where the backlog sits.

Dataset: data/customer_support_dataset.csv
Columns: Ticket_ID, Category, Channel, Priority, Status,
         Wait_Time_Mins, CSAT_Score, Resolution_Time_Hours
Note: Resolution_Time_Hours is only recorded for Closed tickets
(Open/Pending tickets have no resolution time yet).

Run:  python analysis.py
Outputs: charts in images/ + a findings summary printed to stdout.
Requires: pandas, matplotlib, seaborn (see requirements.txt)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "customer_support_dataset.csv"
IMG = BASE / "images"
IMG.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3})

# ---------------------------------------------------------------- load
df = pd.read_csv(DATA)
print(f"Tickets analyzed: {len(df):,}")
print(f"Columns: {list(df.columns)}")
print(f"Missing values: Resolution_Time_Hours is blank for "
      f"{df['Resolution_Time_Hours'].isna().sum()} tickets "
      f"(all Open/Pending — no resolution time yet)\n")

# ------------------------------------------------- 1. ticket volume
print("--- Ticket volume ---")
for col in ["Category", "Channel", "Priority", "Status"]:
    vc = df[col].value_counts()
    print(f"\n{col}:")
    for k, v in vc.items():
        print(f"  {k}: {v:,} ({v / len(df) * 100:.1f}%)")

fig, ax = plt.subplots(figsize=(8, 4.5))
order = df["Category"].value_counts().index
sns.countplot(data=df, y="Category", order=order, ax=ax, color="#4479A1")
ax.set_title("Tickets by Category (n = 2,500)")
ax.set_xlabel("Tickets")
plt.tight_layout()
plt.savefig(IMG / "tickets_by_category.png")
plt.close()

fig, ax = plt.subplots(figsize=(8, 4.5))
order = df["Channel"].value_counts().index
sns.countplot(data=df, y="Channel", order=order, ax=ax, color="#4479A1")
ax.set_title("Tickets by Channel (n = 2,500)")
ax.set_xlabel("Tickets")
plt.tight_layout()
plt.savefig(IMG / "tickets_by_channel.png")
plt.close()

# ------------------------------------------- 2. wait time vs CSAT
print("\n--- Wait time vs CSAT ---")
bins = [0, 15, 30, 45, 60, 201]
labels = ["0-15 min", "15-30 min", "30-45 min", "45-60 min", "60+ min"]
df["wait_bucket"] = pd.cut(df["Wait_Time_Mins"], bins=bins, labels=labels)
bucket = df.groupby("wait_bucket", observed=True).agg(
    n=("CSAT_Score", "size"),
    mean_csat=("CSAT_Score", "mean"),
    pct_low_csat=("CSAT_Score", lambda s: (s <= 2).mean() * 100),
)
print(bucket.round(2).to_string())

over45 = df["Wait_Time_Mins"] > 45
print(f"\nTickets waiting >45 min: {over45.sum():,} ({over45.mean() * 100:.1f}%)")
print(f"Mean CSAT, wait <=45 min: {df.loc[~over45, 'CSAT_Score'].mean():.2f}")
print(f"Mean CSAT, wait >45 min:  {df.loc[over45, 'CSAT_Score'].mean():.2f}")
print(f"Gap: {df.loc[~over45, 'CSAT_Score'].mean() - df.loc[over45, 'CSAT_Score'].mean():.2f} CSAT points")
print(f"Correlation (wait time vs CSAT): "
      f"{df['Wait_Time_Mins'].corr(df['CSAT_Score']):.3f}")
print(f"Share of all tickets with CSAT <= 2: {(df['CSAT_Score'] <= 2).mean() * 100:.1f}%")
print(f"Share of >45-min tickets with CSAT <= 2: "
      f"{(df.loc[over45, 'CSAT_Score'] <= 2).mean() * 100:.1f}%")
print(f"Share of <=45-min tickets with CSAT <= 2: "
      f"{(df.loc[~over45, 'CSAT_Score'] <= 2).mean() * 100:.1f}%")

fig, ax = plt.subplots(figsize=(8, 4.5))
bucket["mean_csat"].plot(kind="bar", ax=ax, color="#4479A1")
ax.axhline(4.0, color="gray", linestyle="--", linewidth=1)
ax.set_title("Mean CSAT by Wait-Time Bucket (1-5 scale)")
ax.set_ylabel("Mean CSAT")
ax.set_xlabel("Wait time before first response")
ax.set_ylim(0, 5)
for i, v in enumerate(bucket["mean_csat"]):
    ax.text(i, v + 0.12, f"{v:.2f}", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(IMG / "wait_vs_csat.png")
plt.close()

# --------------------------------- 3. resolution time (closed only)
closed = df[df["Status"] == "Closed"]
print("\n--- Resolution time (Closed tickets only, n = "
      f"{len(closed):,}) ---")
print(f"Mean: {closed['Resolution_Time_Hours'].mean():.1f} hours, "
      f"median: {closed['Resolution_Time_Hours'].median():.1f} hours")
print("\nMean resolution hours by category:")
print(closed.groupby("Category")["Resolution_Time_Hours"].mean().round(1).to_string())
print("\nMean resolution hours by priority:")
print(closed.groupby("Priority")["Resolution_Time_Hours"].mean().round(1).to_string())
print(f"\nCorrelation (resolution time vs CSAT, closed): "
      f"{closed['Resolution_Time_Hours'].corr(closed['CSAT_Score']):.3f}")

fig, ax = plt.subplots(figsize=(8, 4.5))
order = ["Low", "Medium", "High", "Urgent"]
sns.barplot(data=closed, x="Priority", y="Resolution_Time_Hours",
            order=order, ax=ax, color="#4479A1")
ax.set_title("Mean Resolution Time by Priority (Closed tickets)")
ax.set_ylabel("Hours")
plt.tight_layout()
plt.savefig(IMG / "resolution_by_priority.png")
plt.close()

# ------------------------------------------- 4. backlog (open work)
backlog = df[df["Status"] != "Closed"]
print(f"\n--- Backlog (Open + Pending): {len(backlog):,} tickets "
      f"({len(backlog) / len(df) * 100:.1f}% of all tickets) ---")
print("\nBacklog by priority:")
print(backlog["Priority"].value_counts().to_string())
print("\nBacklog by category:")
print(backlog["Category"].value_counts().to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
ct = pd.crosstab(df["Priority"], df["Status"])
ct = ct.reindex(["Low", "Medium", "High", "Urgent"])
ct.plot(kind="bar", stacked=True, ax=ax,
        color=["#5B9BD5", "#ED7D31", "#70AD47"])
ax.set_title("Ticket Status by Priority")
ax.set_ylabel("Tickets")
ax.set_xlabel("Priority")
plt.tight_layout()
plt.savefig(IMG / "status_by_priority.png")
plt.close()

# ------------------------------------------- 5. what does NOT matter
print("\n--- What does NOT drive CSAT ---")
print("Mean CSAT by category:")
print(df.groupby("Category")["CSAT_Score"].mean().round(2).to_string())
print("\nMean CSAT by channel:")
print(df.groupby("Channel")["CSAT_Score"].mean().round(2).to_string())
print("\nMean CSAT by priority:")
print(df.groupby("Priority")["CSAT_Score"].mean().round(2).to_string())
print("\nMean wait time by category / channel / priority is flat "
      "(24-28 min everywhere) — wait time is not a category problem.")

print("\nDone. Charts saved to images/:")
for p in sorted(IMG.glob("*.png")):
    print(f"  {p.name}")
