"""
Análisis estadístico avanzado con énfasis en rigor científico.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional


def analyze_normality(df: pd.DataFrame, column: str) -> Dict:
    """
    Prueba de normalidad usando Shapiro-Wilk y Kolmogorov-Smirnov.
    
    Args:
        df: DataFrame
        column: Nombre de la columna
    
    Returns:
        Resultados de pruebas de normalidad
    """
    data = df[column].dropna()
    
    shapiro_stat, shapiro_p = stats.shapiro(data)
    ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
    
    return {
        "Shapiro-Wilk": {"estadístico": shapiro_stat, "p-valor": shapiro_p},
        "Kolmogorov-Smirnov": {"estadístico": ks_stat, "p-valor": ks_p},
        "Interpretación": "Distribución normal" if shapiro_p > 0.05 else "Distribución NO normal"
    }


def analyze_homogeneity(df: pd.DataFrame, groups_col: str, values_col: str) -> Dict:
    """
    Prueba de homocedasticidad de Levene.
    
    Args:
        df: DataFrame
        groups_col: Columna de grupos
        values_col: Columna de valores
    
    Returns:
        Resultados de Levene
    """
    groups = df[groups_col].unique()
    group_data = [df[df[groups_col] == g][values_col].dropna().values for g in groups]
    
    levene_stat, levene_p = stats.levene(*group_data)
    
    return {
        "Estadístico de Levene": levene_stat,
        "p-valor": levene_p,
        "Interpretación": "Varianzas homogéneas" if levene_p > 0.05 else "Varianzas NO homogéneas"
    }


def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calcula la d de Cohen (tamaño del efecto).
    
    Args:
        group1: Primer grupo de datos
        group2: Segundo grupo de datos
    
    Returns:
        d de Cohen
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    d = (np.mean(group1) - np.mean(group2)) / pooled_std
    
    return d


def t_test_independent(df: pd.DataFrame, groups_col: str, values_col: str) -> Dict:
    """
    Prueba t de Student para muestras independientes.
    
    Args:
        df: DataFrame
        groups_col: Columna de grupos
        values_col: Columna de valores
    
    Returns:
        Resultados de la prueba t
    """
    groups = df[groups_col].unique()
    if len(groups) != 2:
        return {"error": "Esta prueba requiere exactamente 2 grupos"}
    
    group1 = df[df[groups_col] == groups[0]][values_col].dropna().values
    group2 = df[df[groups_col] == groups[1]][values_col].dropna().values
    
    t_stat, p_value = stats.ttest_ind(group1, group2)
    cohens_d = calculate_cohens_d(group1, group2)
    
    # Intervalo de confianza al 95%
    se = np.sqrt((np.var(group1, ddof=1) / len(group1)) + (np.var(group2, ddof=1) / len(group2)))
    df_val = len(group1) + len(group2) - 2
    t_crit = stats.t.ppf(0.975, df_val)
    mean_diff = np.mean(group1) - np.mean(group2)
    ci_lower = mean_diff - t_crit * se
    ci_upper = mean_diff + t_crit * se
    
    return {
        "t-estadístico": t_stat,
        "p-valor": p_value,
        "d de Cohen": cohens_d,
        "Intervalo de Confianza (95%)": (ci_lower, ci_upper),
        "Significancia": "Significativo" if p_value < 0.05 else "No significativo",
        "Tamaño del efecto": _interpret_cohens_d(cohens_d)
    }


def anova_test(df: pd.DataFrame, groups_col: str, values_col: str) -> Dict:
    """
    ANOVA de una vía.
    
    Args:
        df: DataFrame
        groups_col: Columna de grupos
        values_col: Columna de valores
    
    Returns:
        Resultados de ANOVA
    """
    groups = df[groups_col].unique()
    group_data = [df[df[groups_col] == g][values_col].dropna().values for g in groups]
    
    f_stat, p_value = stats.f_oneway(*group_data)
    
    # Eta-cuadrado (tamaño del efecto)
    grand_mean = np.concatenate(group_data).mean()
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_data)
    ss_total = sum((x - grand_mean)**2 for g in group_data for x in g)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0
    
    return {
        "F-estadístico": f_stat,
        "p-valor": p_value,
        "Eta-cuadrado": eta_squared,
        "Significancia": "Significativo" if p_value < 0.05 else "No significativo",
        "Tamaño del efecto": _interpret_eta_squared(eta_squared)
    }


def correlation_analysis(df: pd.DataFrame, col1: str, col2: str) -> Dict:
    """
    Análisis de correlación de Pearson.
    
    Args:
        df: DataFrame
        col1: Primera columna
        col2: Segunda columna
    
    Returns:
        Resultados de correlación
    """
    data1 = df[col1].dropna()
    data2 = df[col2].dropna()
    
    # Asegurar mismo tamaño
    min_len = min(len(data1), len(data2))
    data1 = data1.iloc[:min_len].values
    data2 = data2.iloc[:min_len].values
    
    r, p_value = stats.pearsonr(data1, data2)
    
    # Intervalo de confianza de Fisher
    z = 0.5 * np.log((1 + r) / (1 - r))
    se = 1 / np.sqrt(len(data1) - 3)
    z_crit = stats.norm.ppf(0.975)
    ci_lower = np.tanh(z - z_crit * se)
    ci_upper = np.tanh(z + z_crit * se)
    
    return {
        "r de Pearson": r,
        "p-valor": p_value,
        "Intervalo de Confianza (95%)": (ci_lower, ci_upper),
        "Significancia": "Significativo" if p_value < 0.05 else "No significativo",
        "Magnitud": _interpret_correlation(r)
    }


def _interpret_cohens_d(d: float) -> str:
    """Interpreta d de Cohen según criterios convencionales."""
    d = abs(d)
    if d < 0.2:
        return "Negligible"
    elif d < 0.5:
        return "Pequeño"
    elif d < 0.8:
        return "Mediano"
    else:
        return "Grande"


def _interpret_eta_squared(eta2: float) -> str:
    """Interpreta eta-cuadrado."""
    if eta2 < 0.01:
        return "Negligible"
    elif eta2 < 0.06:
        return "Pequeño"
    elif eta2 < 0.14:
        return "Mediano"
    else:
        return "Grande"


def _interpret_correlation(r: float) -> str:
    """Interpreta correlación de Pearson."""
    r = abs(r)
    if r < 0.1:
        return "Negligible"
    elif r < 0.3:
        return "Pequeña"
    elif r < 0.5:
        return "Mediana"
    else:
        return "Grande"


def generate_statistical_report(df: pd.DataFrame, numeric_cols: list) -> str:
    """
    Genera un reporte estadístico completo.
    
    Args:
        df: DataFrame
        numeric_cols: Lista de columnas numéricas a analizar
    
    Returns:
        Reporte en texto
    """
    report = "REPORTE ESTADÍSTICO DESCRIPTIVO\n"
    report += "=" * 50 + "\n\n"
    
    for col in numeric_cols:
        if col in df.columns:
            data = df[col].dropna()
            report += f"\n{col}:\n"
            report += f"  n = {len(data)}\n"
            report += f"  M = {data.mean():.4f}\n"
            report += f"  DE = {data.std():.4f}\n"
            report += f"  Mín = {data.min():.4f}\n"
            report += f"  Máx = {data.max():.4f}\n"
            report += f"  Mediana = {data.median():.4f}\n"
            report += f"  IQR = {data.quantile(0.75) - data.quantile(0.25):.4f}\n"
    
    return report
