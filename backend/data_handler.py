import pandas as pd
import re
from pathlib import Path

EXCEL_PATH = Path(__file__).parent.parent / "Vendor details anonymized.xlsx"

_df: pd.DataFrame | None = None

AFFILIATES = [
    "Austria", "Middle-East", "Benelux", "Oevel Plant", "East Hub",
    "Balkans", "Central Europe", "Nordics", "France", "Eurovision",
    "Germany", "India", "Israel", "Italy", "Iberia", "Russia & CIS",
    "South Africa", "Lachen Plant", "Switzerland", "Turkey", "UK"
]

LEVEL1_CATEGORIES = [
    "SUPPLY CHAIN", "NON-PROCURABLE", "ADVERTISING & PROMOTIONS",
    "STORE MANAGEMENT", "CORPORATE SERVICES", "STORE CONSTRUCTION",
    "INFORMATION TECHNOLOGY", "FACILITY CONSTRUCTION", "FACILITY MANAGEMENT",
    "TRAVEL, MEETINGS AND EVENTS", "UNCLASSIFIED", "INGREDIENTS", "R&D AND QA"
]

SCOPES = ["LOCAL", "REGIONAL", "GLOBAL"]


def load_data() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_excel(EXCEL_PATH)
        _df = _df[~_df['Affiliate'].isna()]
        _df['Vendor Name'] = _df['Vendor Name'].fillna('').str.strip()
        _df['Spend (USD)'] = pd.to_numeric(_df['Spend (USD)'], errors='coerce').fillna(0)
    return _df


def _fmt_usd(val: float) -> str:
    return f"${val:,.2f}"


def query_data(question: str) -> str:
    df = load_data()
    q = question.upper()

    # Detect filters from question text
    affiliate_filter = None
    for aff in AFFILIATES:
        if aff.upper() in q:
            affiliate_filter = aff
            break

    cat_filter = None
    for cat in LEVEL1_CATEGORIES:
        if cat in q or cat.split()[0] in q:
            cat_filter = cat
            break

    scope_filter = None
    for scope in SCOPES:
        if scope in q:
            scope_filter = scope
            break

    # Detect vendor name (quoted or after "vendor"/"dobavljac")
    vendor_filter = None
    vendor_match = re.search(r'"([^"]+)"', question)
    if vendor_match:
        vendor_filter = vendor_match.group(1).upper()
    else:
        vendor_kw = re.search(r'(?:vendor|dobavlja[cč]|supplier)\s+(?:named?\s+)?([A-Za-z].{3,30}?)(?:\s|$|\?|,)', question, re.I)
        if vendor_kw:
            vendor_filter = vendor_kw.group(1).upper().strip()

    # Apply filters
    filtered = df.copy()
    if affiliate_filter:
        filtered = filtered[filtered['Affiliate'].str.upper() == affiliate_filter.upper()]
    if cat_filter:
        filtered = filtered[filtered['Level 1'].str.upper() == cat_filter.upper()]
    if scope_filter:
        filtered = filtered[filtered['Supplier Scope'].str.upper() == scope_filter.upper()]
    if vendor_filter:
        filtered = filtered[filtered['Vendor Name'].str.upper().str.contains(vendor_filter, na=False)]

    # Detect what kind of answer is needed
    q_lower = question.lower()

    # Top vendors question
    if any(w in q_lower for w in ['top', 'largest', 'biggest', 'highest', 'most', 'najveci', 'najveći', 'top dobavlja']):
        n = 10
        num_match = re.search(r'\b(\d+)\b', question)
        if num_match:
            n = min(int(num_match.group(1)), 50)
        result = (
            filtered.groupby('Vendor Name')['Spend (USD)']
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )
        lines = [f"Top {n} vendors by spend" + (f" in {affiliate_filter}" if affiliate_filter else "") + (f" [{cat_filter}]" if cat_filter else "") + ":"]
        for i, row in result.iterrows():
            lines.append(f"{i+1}. {row['Vendor Name']}: {_fmt_usd(row['Spend (USD)'])}")
        return "\n".join(lines)

    # Spend by affiliate/country
    if any(w in q_lower for w in ['by country', 'by affiliate', 'per country', 'per affiliate', 'by region', 'po zemlji', 'po drzavi', 'po državi']):
        result = (
            filtered.groupby('Affiliate')['Spend (USD)']
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        lines = ["Spend by affiliate:"]
        for _, row in result.iterrows():
            lines.append(f"- {row['Affiliate']}: {_fmt_usd(row['Spend (USD)'])}")
        return "\n".join(lines)

    # Spend by category
    if any(w in q_lower for w in ['by category', 'categories', 'kategorij', 'per category', 'by level']):
        result = (
            filtered.groupby('Level 1')['Spend (USD)']
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        lines = ["Spend by Level 1 category:"]
        for _, row in result.iterrows():
            lines.append(f"- {row['Level 1']}: {_fmt_usd(row['Spend (USD)'])}")
        return "\n".join(lines)

    # Managed supplier status
    if any(w in q_lower for w in ['managed', 'preferred', 'whitespace', 'non-addressable', 'klasifikacij', 'status']):
        result = (
            filtered.groupby('Managed Supplier')['Spend (USD)']
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        lines = ["Spend by supplier classification:"]
        for _, row in result.iterrows():
            lines.append(f"- {row['Managed Supplier']}: {_fmt_usd(row['Spend (USD)'])}")
        return "\n".join(lines)

    # Total spend question
    if any(w in q_lower for w in ['total', 'ukupno', 'sum', 'spend', 'potrosnja', 'potrošnja', 'how much']):
        total = filtered['Spend (USD)'].sum()
        vendor_count = filtered['Vendor Name'].nunique()
        record_count = len(filtered)
        parts = []
        if affiliate_filter:
            parts.append(f"affiliate: {affiliate_filter}")
        if cat_filter:
            parts.append(f"category: {cat_filter}")
        if scope_filter:
            parts.append(f"scope: {scope_filter}")
        filter_str = f" (filters: {', '.join(parts)})" if parts else ""
        return f"Total spend{filter_str}: {_fmt_usd(total)}\nVendors: {vendor_count}\nTransactions: {record_count:,}"

    # Vendor detail lookup
    if vendor_filter and len(filtered) > 0:
        agg = (
            filtered.groupby('Vendor Name')
            .agg(
                Total_Spend=('Spend (USD)', 'sum'),
                Transactions=('Spend (USD)', 'count'),
                Affiliates=('Affiliate', lambda x: ', '.join(sorted(x.unique()))),
                Categories=('Level 1', lambda x: ', '.join(sorted(x.unique()))),
                Scope=('Supplier Scope', lambda x: ', '.join(sorted(x.unique()))),
                Status=('Managed Supplier', lambda x: ', '.join(sorted(x.unique()))),
            )
            .sort_values('Total_Spend', ascending=False)
            .head(10)
            .reset_index()
        )
        lines = [f"Vendors matching '{vendor_filter}':"]
        for _, row in agg.iterrows():
            lines.append(
                f"\n{row['Vendor Name']}\n"
                f"  Spend: {_fmt_usd(row['Total_Spend'])}\n"
                f"  Transactions: {row['Transactions']}\n"
                f"  Affiliates: {row['Affiliates']}\n"
                f"  Categories: {row['Categories']}\n"
                f"  Scope: {row['Scope']}\n"
                f"  Status: {row['Status']}"
            )
        return "\n".join(lines)

    # General overview if no specific query detected
    total = filtered['Spend (USD)'].sum()
    vendor_count = filtered['Vendor Name'].nunique()
    aff_count = filtered['Affiliate'].nunique()
    top_vendors = (
        filtered.groupby('Vendor Name')['Spend (USD)']
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top_cats = (
        filtered.groupby('Level 1')['Spend (USD)']
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    lines = [
        f"Dataset overview{' (filtered)' if any([affiliate_filter, cat_filter, scope_filter]) else ''}:",
        f"Total spend: {_fmt_usd(total)}",
        f"Unique vendors: {vendor_count:,}",
        f"Affiliates: {aff_count}",
        "",
        "Top 5 vendors by spend:",
    ]
    for _, row in top_vendors.iterrows():
        lines.append(f"  - {row['Vendor Name']}: {_fmt_usd(row['Spend (USD)'])}")
    lines.append("\nTop 5 categories by spend:")
    for _, row in top_cats.iterrows():
        lines.append(f"  - {row['Level 1']}: {_fmt_usd(row['Spend (USD)'])}")
    return "\n".join(lines)


def get_dataset_summary() -> str:
    df = load_data()
    total = df['Spend (USD)'].sum()
    return (
        f"Dataset: EMEA Vendor Spend, Fiscal Year 2026\n"
        f"Total records: {len(df):,}\n"
        f"Total spend: {_fmt_usd(total)}\n"
        f"Affiliates ({df['Affiliate'].nunique()}): {', '.join(sorted(df['Affiliate'].dropna().unique()))}\n"
        f"Level 1 categories: {', '.join(sorted(df['Level 1'].dropna().unique()))}\n"
        f"Supplier scopes: {', '.join(sorted(df['Supplier Scope'].dropna().unique()))}\n"
        f"Managed types: {', '.join(df['Managed Supplier'].dropna().unique())}"
    )
