"""Editorial design tokens and CSS stylesheet for Onboarding assistant.

Directly integrated from Google Stitch MCP 'Warm Editorial Dev' design system.
Enforces high visual contrast and distinct differentiation between the left-hand navigation
panel (deep conifer slate #0E1B15) and the editorial alabaster main dashboard canvas (#F8F9F8).
Preserves Newsreader serif, Inter sans, and JetBrains Mono typographic hierarchy.
Prohibits default Streamlit pink hues, balloons, drop-shadows, and chat bubbles.
"""

from __future__ import annotations

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');

:root {
    /* Main Dashboard Light Canvas */
    --bg-page: #F8F9F8;
    --bg-surface: #FFFFFF;
    --bg-surface-subtle: #F5F7F5;
    --bg-surface-low: #EEF2EE;
    --text-ink: #111827;
    --text-secondary: #2D3748;
    --text-muted: #64748B;
    --text-faint: #94A3B8;
    --border-hairline: #E2E8F0;
    --border-subtle: #EDF2F7;
    
    /* Conifer Green & Forest Semantic Tokens */
    --accent-primary: #1B4332;
    --accent-hover: #2D6A4F;
    --accent-tint: #D8F3DC;
    --accent-border: #B7E4C7;
    --live-primary: #2B4C7E;
    --live-tint: #E6ECF4;
    
    /* High-Contrast Differentiated Left Sidebar (Deep Conifer Slate) */
    --bg-sidebar: #0E1B15;
    --bg-sidebar-card: #14261E;
    --bg-sidebar-card-hover: #193127;
    --bg-sidebar-card-low: #0B1611;
    --border-sidebar: #1E382B;
    --border-sidebar-subtle: #162C21;
    --text-sidebar-heading: #FFFFFF;
    --text-sidebar-body: #EBF2F7;
    --text-sidebar-muted: #86AF99;
    --text-sidebar-faint: #5C7A6B;
    --sidebar-accent-bright: #34D399;
    --sidebar-accent-tint: rgba(52, 211, 153, 0.15);
    --sidebar-accent-border: rgba(52, 211, 153, 0.28);
    
    /* Action & Status Semantic Tokens */
    --proposal-primary: #D97706;
    --proposal-hover: #B45309;
    --proposal-tint: #FFFBEB;
    --proposal-border: #FDE68A;
    --proposal-badge: #FEF3C7;
    --error-primary: #B91C1C;
    --error-tint: #FEE2E2;
    
    /* Typography */
    --font-serif: 'Newsreader', Georgia, serif;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace;
    
    /* Geometry & Depth */
    --radius: 4px;
    --radius-lg: 8px;
    --radius-sm: 2px;
    --shadow-subtle: 0 1px 3px 0 rgba(17, 24, 28, 0.05), 0 1px 2px -1px rgba(17, 24, 28, 0.03);
    --shadow-md: 0 4px 6px -1px rgba(17, 24, 28, 0.08), 0 2px 4px -2px rgba(17, 24, 28, 0.05);
}

/* Global Document Reset */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-page) !important;
    color: var(--text-ink) !important;
    font-family: var(--font-sans) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

[data-testid="stHeader"] {
    background-color: var(--bg-surface) !important;
    border-bottom: 1px solid var(--border-hairline) !important;
}

/* Hide default Streamlit decoration, main menu, and footer */
#MainMenu, footer, [data-testid="stDecoration"] {
    display: none !important;
}

/* ========================================================================= */
/* LEFT SIDEBAR: Deep conifer slate dark theme (#0E1B15) with high contrast  */
/* ========================================================================= */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-sidebar) !important;
    box-shadow: 4px 0 24px 0 rgba(0, 0, 0, 0.22) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.15rem !important;
    padding-right: 1.15rem !important;
}

/* Workspace Brand Header in Sidebar */
.sidebar-workspace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.85rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--border-sidebar);
}

.sidebar-workspace-brand {
    display: flex;
    align-items: center;
    gap: 9px;
}

.sidebar-workspace-logo {
    width: 26px;
    height: 26px;
    border-radius: var(--radius);
    background: #1B4332;
    border: 1px solid #2D6A4F;
    color: #A5D0B9;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-weight: 700;
    font-size: 12px;
}

.sidebar-workspace-title {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    color: #FFFFFF;
    line-height: 1.2;
}

.sidebar-workspace-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-sidebar-muted);
}

.sidebar-branch-pill {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 2px 7px;
    background: #14261E;
    color: #A5D0B9;
    border: 1px solid var(--border-sidebar);
    border-radius: var(--radius-sm);
    font-weight: 500;
}

/* Section Header Labels in Sidebar */
.sidebar-label {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-sidebar-muted) !important;
    margin-bottom: 0.45rem;
    margin-top: 1.15rem;
}

.sidebar-label:first-child {
    margin-top: 0;
}

/* Section Header Labels in Main Dashboard */
.section-label {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent-primary);
    margin-bottom: 0.5rem;
    margin-top: 1.25rem;
}

/* Streamlit Selectbox inside Dark Sidebar (Supports BaseWeb and React-Aria) */
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[role="group"] {
    background-color: var(--bg-sidebar-card) !important;
    border: 1px solid var(--border-sidebar) !important;
    border-radius: var(--radius-lg) !important;
    color: #FFFFFF !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
    transition: border-color 0.15s ease;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] div[role="group"]:hover {
    border-color: #2D6A4F !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] input {
    color: #FFFFFF !important;
    background-color: transparent !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] div[role="group"] button {
    background: transparent !important;
    border: none !important;
    color: var(--text-sidebar-muted) !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
    fill: var(--text-sidebar-muted) !important;
}

/* Dropdown popover listbox options */
div[data-rac=""][role="listbox"],
div[data-baseweb="popover"] ul {
    background-color: #14261E !important;
    border: 1px solid var(--border-sidebar) !important;
    border-radius: var(--radius-lg) !important;
    color: #FFFFFF !important;
}

div[data-rac=""][role="option"],
div[data-baseweb="popover"] li {
    color: #E2E8F0 !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
}

div[data-rac=""][role="option"]:hover,
div[data-rac=""][role="option"][data-focused="true"],
div[data-baseweb="popover"] li:hover {
    background-color: #1F3D30 !important;
    color: #34D399 !important;
}

/* Persona Profile Card in Sidebar */
[data-testid="stSidebar"] .persona-card {
    background-color: var(--bg-sidebar-card) !important;
    border: 1px solid var(--border-sidebar) !important;
    border-radius: var(--radius-lg) !important;
    padding: 12px 14px !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stSidebar"] .persona-header-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

[data-testid="stSidebar"] .persona-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50% !important;
    background-color: #1B4332 !important;
    border: 1px solid #2D6A4F !important;
    color: #C1ECD4 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    flex-shrink: 0;
    box-shadow: 0 0 8px rgba(45, 106, 79, 0.3);
}

[data-testid="stSidebar"] .persona-name {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] .persona-role {
    font-size: 11px !important;
    color: var(--text-sidebar-muted) !important;
}

[data-testid="stSidebar"] .persona-meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid var(--border-sidebar-subtle);
    font-size: 11px;
    font-family: var(--font-mono);
    color: var(--text-sidebar-muted);
}

[data-testid="stSidebar"] .persona-role-highlight {
    color: var(--sidebar-accent-bright) !important;
    font-weight: 600;
}

[data-testid="stSidebar"] .persona-badge {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background-color: var(--sidebar-accent-tint) !important;
    color: var(--sidebar-accent-bright) !important;
    border: 1px solid var(--sidebar-accent-border) !important;
    padding: 2px 7px;
    border-radius: var(--radius-sm);
    font-weight: 600;
}

/* Segmented Progress Tracker in Sidebar */
[data-testid="stSidebar"] .progress-container {
    background-color: var(--bg-sidebar-card) !important;
    border: 1px solid var(--border-sidebar) !important;
    border-radius: var(--radius-lg) !important;
    padding: 12px 14px !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stSidebar"] .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-sidebar-muted) !important;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] .progress-percent-label {
    color: var(--sidebar-accent-bright) !important;
    font-weight: 600;
}

[data-testid="stSidebar"] .segmented-bar {
    display: flex;
    gap: 3px;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] .progress-segment {
    height: 6px;
    flex-grow: 1;
    background-color: #193326 !important;
    border-radius: 2px;
    transition: background-color 0.2s ease;
}

[data-testid="stSidebar"] .progress-segment.filled {
    background-color: var(--sidebar-accent-bright) !important;
    box-shadow: 0 0 6px rgba(52, 211, 153, 0.5) !important;
}

[data-testid="stSidebar"] .progress-text {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-sidebar-muted) !important;
    display: flex;
    justify-content: space-between;
}

/* Upcoming / Next Milestone Card in Sidebar */
.sidebar-next-card {
    background-color: #12221B;
    border: 1px solid #1F3D30;
    border-left: 3px solid var(--sidebar-accent-bright);
    border-radius: var(--radius-lg);
    padding: 11px 13px;
    margin-top: 8px;
    box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.25);
}

.sidebar-next-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.sidebar-next-tag {
    font-family: var(--font-mono);
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--sidebar-accent-tint);
    color: var(--sidebar-accent-bright);
    border: 1px solid var(--sidebar-accent-border);
    padding: 1px 6px;
    border-radius: var(--radius-sm);
}

.sidebar-next-step {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-sidebar-muted);
}

.sidebar-next-title {
    font-size: 12px;
    font-weight: 600;
    color: #FFFFFF;
    line-height: 1.4;
}

/* Action Button in Sidebar (e.g. Ask about next step) */
[data-testid="stSidebar"] .stButton > button {
    background: #1B4332 !important;
    border: 1px solid #2D6A4F !important;
    color: #C1ECD4 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    border-radius: var(--radius) !important;
    width: 100% !important;
    margin-top: 6px !important;
    padding: 0.45rem 0.8rem !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #2D6A4F !important;
    border-color: var(--sidebar-accent-bright) !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(45, 106, 79, 0.4) !important;
}

/* Technical Telemetry / Provenance Cards in Sidebar */
.sidebar-telemetry-card {
    background-color: var(--bg-sidebar-card-low);
    border: 1px solid var(--border-sidebar);
    border-radius: var(--radius-lg);
    padding: 10px 12px;
    box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.2);
    margin-bottom: 0.4rem;
}

.sidebar-telemetry-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.sidebar-telemetry-title {
    font-weight: 600;
    color: #E2E8F0;
    font-size: 11px;
}

.sidebar-telemetry-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--sidebar-accent-bright);
    box-shadow: 0 0 6px var(--sidebar-accent-bright);
}

.sidebar-telemetry-shield {
    font-family: var(--font-mono);
    font-size: 9px;
    background: #14261E;
    color: #A5D0B9;
    padding: 1px 5px;
    border-radius: 2px;
    border: 1px solid var(--border-sidebar);
}

.sidebar-telemetry-body {
    font-size: 11px;
    line-height: 1.45;
    color: var(--text-sidebar-muted);
}

/* ========================================================================= */
/* MAIN DASHBOARD: Editorial Alabaster Canvas with Refined Visual Hierarchy  */
/* ========================================================================= */

/* App Header Chrome */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0 1rem 0;
    margin-bottom: 1.25rem;
    border-bottom: 1px solid var(--border-hairline);
    background-color: transparent;
}

.wordmark {
    font-family: var(--font-serif);
    font-size: 26px;
    font-weight: 600;
    color: var(--text-ink);
    letter-spacing: -0.02em;
}

.repo-chip {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent-primary);
    background-color: var(--accent-tint);
    border: 1px solid var(--accent-border);
    border-radius: var(--radius);
    padding: 3px 8px;
    margin-left: 10px;
    vertical-align: middle;
    font-weight: 600;
}

.model-status-line {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent-primary);
    background-color: var(--bg-surface);
    border: 1px solid var(--accent-border);
    border-radius: var(--radius);
    padding: 4px 10px;
    display: flex;
    align-items: center;
    gap: 7px;
    box-shadow: var(--shadow-subtle);
}

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--accent-primary);
    box-shadow: 0 0 5px rgba(27, 67, 50, 0.5);
}

.status-dot.fallback {
    background-color: var(--proposal-primary);
    box-shadow: 0 0 5px rgba(217, 119, 6, 0.5);
}

/* Horizontal Underlined Tabs (st.radio styling) */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    border-bottom: 1px solid var(--border-hairline);
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}

div[data-testid="stRadio"] label {
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    cursor: pointer !important;
    padding: 6px 12px 10px 12px !important;
    margin-bottom: -1px !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.15s ease, border-color 0.15s ease, background-color 0.15s ease !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
}

div[data-testid="stRadio"] label:hover {
    color: var(--text-ink) !important;
    background-color: rgba(0, 0, 0, 0.02) !important;
}

div[data-testid="stRadio"] label[data-checked="true"],
div[data-testid="stRadio"] div[aria-checked="true"] + label {
    color: var(--accent-primary) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--accent-primary) !important;
    background-color: rgba(27, 67, 50, 0.04) !important;
}

/* Welcome Hero Card */
.welcome-hero {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-left: 4px solid var(--accent-primary);
    border-radius: var(--radius-lg);
    padding: 24px 26px;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-subtle);
}

.hero-tag {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background-color: var(--accent-tint);
    color: var(--accent-primary);
    padding: 2px 7px;
    border-radius: var(--radius-sm);
    margin-bottom: 8px;
    border: 1px solid var(--accent-border);
}

.hero-title {
    font-family: var(--font-serif);
    font-size: 26px;
    font-weight: 500;
    color: var(--text-ink);
    letter-spacing: -0.015em;
    margin-bottom: 8px;
}

.hero-sub {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
    max-width: 720px;
}

/* Prompt Grid in Welcome State */
.prompt-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.prompt-card {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 15px 17px;
    box-shadow: var(--shadow-subtle);
    transition: border-color 0.15s ease, background-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.prompt-card:hover {
    border-color: var(--accent-primary);
    background-color: var(--bg-surface-subtle);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.prompt-card-category {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-primary);
    margin-bottom: 4px;
}

.prompt-card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-ink);
    margin-bottom: 4px;
}

.prompt-card-desc {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.45;
}

/* User Query Card */
.user-query-container {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-left: 4px solid var(--accent-primary);
    border-radius: var(--radius-lg);
    padding: 15px 19px;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-subtle);
}

.user-query-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-primary);
    margin-bottom: 4px;
}

.user-query-text {
    font-family: var(--font-serif);
    font-size: 19px;
    font-weight: 500;
    line-height: 1.4;
    color: var(--text-ink);
}

/* Assistant Answer Card */
.answer-container {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-subtle);
}

.answer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    margin-bottom: 14px;
    border-bottom: 1px solid var(--border-subtle);
}

.answer-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background-color: var(--accent-tint);
    color: var(--accent-primary);
    border: 1px solid var(--accent-border);
    padding: 2px 8px;
    border-radius: var(--radius-sm);
}

.answer-body {
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.65;
    color: var(--text-ink);
}

.answer-body p {
    margin-bottom: 0.85rem;
}

.answer-body ul, .answer-body ol {
    margin-left: 1.25rem;
    margin-bottom: 0.85rem;
}

.answer-body code {
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    background-color: var(--bg-surface-subtle) !important;
    border: 1px solid var(--border-hairline) !important;
    padding: 2px 6px !important;
    border-radius: var(--radius-sm) !important;
    color: var(--accent-primary) !important;
}

.answer-body pre {
    background-color: var(--bg-surface-subtle) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius) !important;
    padding: 14px !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    overflow-x: auto !important;
}

/* Collapsible Execution Trace */
details.trace-details {
    background-color: var(--bg-surface-subtle);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 10px 14px;
    margin-bottom: 0.75rem;
    font-family: var(--font-mono);
    font-size: 11px;
}

details.trace-details summary {
    cursor: pointer;
    color: var(--text-muted);
    font-weight: 500;
    user-select: none;
}

details.trace-details summary:hover {
    color: var(--text-ink);
}

.trace-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-top: 1px solid var(--border-subtle);
    margin-top: 5px;
}

.trace-row.running {
    animation: opacityPulse 1.2s infinite ease-in-out;
}

@keyframes opacityPulse {
    0% { opacity: 0.45; }
    50% { opacity: 1.0; }
    100% { opacity: 0.45; }
}

/* Source Citation Chips */
.sources-footer {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 1rem;
    padding-top: 0.85rem;
    border-top: 1px solid var(--border-subtle);
}

.source-chip {
    font-family: var(--font-mono);
    font-size: 11px;
    text-decoration: none;
    padding: 3px 9px;
    border-radius: var(--radius-sm);
    display: inline-block;
    transition: background-color 0.15s ease;
    font-weight: 500;
}

.source-chip.local {
    background-color: var(--accent-tint);
    color: var(--accent-primary);
    border: 1px solid var(--accent-border);
}

.source-chip.local:hover {
    background-color: #c4ebd0;
}

.source-chip.live {
    background-color: var(--live-tint);
    color: var(--live-primary);
    border: 1px solid rgba(43, 76, 126, 0.25);
}

.source-chip.live:hover {
    background-color: #dce5f0;
}

/* Proposal Card (Stitch Amber Proposal System) */
.proposal-card {
    background-color: var(--proposal-tint);
    border: 2px solid var(--proposal-border);
    border-radius: var(--radius-lg);
    padding: 16px 18px;
    margin: 1.2rem 0;
    box-shadow: 0 2px 4px 0 rgba(217, 119, 6, 0.06);
}

.proposal-title {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--proposal-primary);
    margin-bottom: 6px;
}

.proposal-body {
    font-family: var(--font-sans);
    font-size: 14px;
    color: var(--text-ink);
    line-height: 1.5;
    margin-bottom: 12px;
}

/* Stage / Phase Header in Path View */
.phase-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border-hairline);
}

.phase-header:first-of-type {
    margin-top: 1rem;
}

.phase-title {
    font-family: var(--font-serif);
    font-size: 18px;
    font-weight: 500;
    color: var(--text-ink);
}

.phase-meta {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
}

/* Path View Step Row */
.step-row {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-left: 3px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 14px 18px;
    margin-bottom: 11px;
    box-shadow: var(--shadow-subtle);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.step-row:hover {
    border-color: #CBD5E1;
    box-shadow: var(--shadow-md);
}

.step-row.done {
    border-left-color: var(--accent-primary);
    background-color: #F8FCF9;
}

.step-row.in_progress {
    border-left-color: var(--proposal-primary);
    background-color: #FFFDF7;
}

.step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.step-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-ink);
}

.step-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: var(--radius-sm);
    font-weight: 600;
}

.step-badge.done {
    background-color: var(--accent-tint);
    color: var(--accent-primary);
    border: 1px solid var(--accent-border);
}

.step-badge.next {
    background-color: var(--proposal-badge);
    color: var(--proposal-primary);
    border: 1px solid var(--proposal-border);
}

.step-badge.todo {
    background-color: var(--bg-surface-subtle);
    color: var(--text-muted);
    border: 1px solid var(--border-hairline);
}

/* Filter Summary Bar */
.filter-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 10px 14px;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-subtle);
}

/* Restyle chat input */
[data-testid="stChatInput"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-subtle) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent-primary) !important;
    outline: 2px solid var(--accent-tint) !important;
}

[data-testid="stChatInputTextArea"] {
    font-family: var(--font-sans) !important;
    color: var(--text-ink) !important;
}

/* Restyle default buttons */
button[kind="secondary"], button[kind="primary"] {
    border-radius: var(--radius) !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

button[kind="primary"] {
    background-color: var(--accent-primary) !important;
    border-color: var(--accent-primary) !important;
    color: #FFFFFF !important;
    font-weight: 500 !important;
}

button[kind="primary"]:hover {
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}

button[kind="secondary"] {
    background-color: var(--bg-surface) !important;
    border-color: var(--border-hairline) !important;
    color: var(--text-ink) !important;
}

button[kind="secondary"]:hover {
    border-color: var(--accent-primary) !important;
    color: var(--accent-primary) !important;
    background-color: var(--bg-surface-subtle) !important;
}
</style>
"""


def get_css() -> str:
    """Return the complete application CSS string."""
    return THEME_CSS
