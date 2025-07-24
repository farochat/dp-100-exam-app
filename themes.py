"""Module for themes collection."""

THEMES = {
    "One Dark": {
        "bg": "#282c34",
        "text": "#abb2bf",
        "button_bg": "#3b4048",
        "button_text": "#e5c07b",
        "button_border": "#528bff",
        "hover_bg": "#3e4451",
        "hover_text": "#98c379",
        "hover_border": "#56b6c2",
        "heading": "#61afef",
        "progress": "#98c379",
        "radio_bg": "#353b45",
        "success_bg": "rgba(152, 195, 121, 0.2)",
        "success_text": "#98c379",
        "success_border": "#98c379",
        "info_bg": "rgba(97, 175, 239, 0.2)",
        "info_text": "#61afef",
        "info_border": "#61afef",
        "warning_bg": "rgba(229, 192, 123, 0.2)",
        "warning_text": "#e5c07b",
        "warning_border": "#e5c07b",
        "error_bg": "rgba(224, 108, 117, 0.2)",
        "error_text": "#e06c75",
        "error_border": "#e06c75",
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "text": "#839496",
        "button_bg": "#073642",
        "button_text": "#b58900",
        "button_border": "#268bd2",
        "hover_bg": "#073642",
        "hover_text": "#2aa198",
        "hover_border": "#859900",
        "heading": "#268bd2",
        "progress": "#859900",
        "radio_bg": "#073642",
        "success_bg": "rgba(133, 153, 0, 0.2)",
        "success_text": "#859900",
        "success_border": "#859900",
        "info_bg": "rgba(38, 139, 210, 0.2)",
        "info_text": "#268bd2",
        "info_border": "#268bd2",
        "warning_bg": "rgba(181, 137, 0, 0.2)",
        "warning_text": "#b58900",
        "warning_border": "#b58900",
        "error_bg": "rgba(220, 50, 47, 0.2)",
        "error_text": "#dc322f",
        "error_border": "#dc322f",
    },
    "Monokai": {
        "bg": "#272822",
        "text": "#f8f8f2",
        "button_bg": "#3e3d32",
        "button_text": "#e6db74",
        "button_border": "#66d9ef",
        "hover_bg": "#49483e",
        "hover_text": "#a6e22e",
        "hover_border": "#fd971f",
        "heading": "#66d9ef",
        "progress": "#a6e22e",
        "radio_bg": "#3e3d32",
        "success_bg": "rgba(166, 226, 46, 0.2)",
        "success_text": "#a6e22e",
        "success_border": "#a6e22e",
        "info_bg": "rgba(102, 217, 239, 0.2)",
        "info_text": "#66d9ef",
        "info_border": "#66d9ef",
        "warning_bg": "rgba(230, 219, 116, 0.2)",
        "warning_text": "#e6db74",
        "warning_border": "#e6db74",
        "error_bg": "rgba(249, 38, 114, 0.2)",
        "error_text": "#f92672",
        "error_border": "#f92672",
    },
    "Dracula": {
        "bg": "#282a36",
        "text": "#f8f8f2",
        "button_bg": "#44475a",
        "button_text": "#f1fa8c",
        "button_border": "#8be9fd",
        "hover_bg": "#44475a",
        "hover_text": "#50fa7b",
        "hover_border": "#ff79c6",
        "heading": "#8be9fd",
        "progress": "#50fa7b",
        "radio_bg": "#44475a",
        "success_bg": "rgba(80, 250, 123, 0.2)",
        "success_text": "#50fa7b",
        "success_border": "#50fa7b",
        "info_bg": "rgba(139, 233, 253, 0.2)",
        "info_text": "#8be9fd",
        "info_border": "#8be9fd",
        "warning_bg": "rgba(241, 250, 140, 0.2)",
        "warning_text": "#f1fa8c",
        "warning_border": "#f1fa8c",
        "error_bg": "rgba(255, 85, 85, 0.2)",
        "error_text": "#ff5555",
        "error_border": "#ff5555",
    },
    "Nord": {
        "bg": "#2e3440",
        "text": "#d8dee9",
        "button_bg": "#3b4252",
        "button_text": "#ebcb8b",
        "button_border": "#88c0d0",
        "hover_bg": "#434c5e",
        "hover_text": "#a3be8c",
        "hover_border": "#81a1c1",
        "heading": "#88c0d0",
        "progress": "#a3be8c",
        "radio_bg": "#3b4252",
        "success_bg": "rgba(163, 190, 140, 0.2)",
        "success_text": "#a3be8c",
        "success_border": "#a3be8c",
        "info_bg": "rgba(136, 192, 208, 0.2)",
        "info_text": "#88c0d0",
        "info_border": "#88c0d0",
        "warning_bg": "rgba(235, 203, 139, 0.2)",
        "warning_text": "#ebcb8b",
        "warning_border": "#ebcb8b",
        "error_bg": "rgba(191, 97, 106, 0.2)",
        "error_text": "#bf616a",
        "error_border": "#bf616a",
    },
}


def get_theme_css(theme_name):
    """Return CSS for the selected theme."""
    theme = THEMES.get(theme_name, THEMES["One Dark"])

    css = f"""
    <style>
    .stApp {{
        background-color: {theme["bg"]};
        color: {theme["text"]};
    }}
    .stButton>button {{
        background-color: {theme["button_bg"]};
        color: {theme["button_text"]};
        border: 1px solid {theme["button_border"]};
    }}
    .stButton>button:hover {{
        background-color: {theme["hover_bg"]};
        color: {theme["hover_text"]};
        border: 1px solid {theme["hover_border"]};
    }}
    .stMarkdown {{
        color: {theme["text"]};
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {theme["heading"]};
    }}
    .stProgress > div > div {{
        background-color: {theme["progress"]};
    }}
    .stRadio > div {{
        background-color: {theme["radio_bg"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stSuccess {{
        background-color: {theme["success_bg"]};
        color: {theme["success_text"]};
        border: 1px solid {theme["success_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stInfo {{
        background-color: {theme["info_bg"]};
        color: {theme["info_text"]};
        border: 1px solid {theme["info_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stWarning {{
        background-color: {theme["warning_bg"]};
        color: {theme["warning_text"]};
        border: 1px solid {theme["warning_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stError {{
        background-color: {theme["error_bg"]};
        color: {theme["error_text"]};
        border: 1px solid {theme["error_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    </style>
    """

    return css


def get_themes_list():
    """Return keys."""
    return list(THEMES)
