"""Présentation uniquement. Aucun calcul de classification, priorité ou regroupement."""
from html import escape
from pathlib import Path
import re
import unicodedata
import streamlit as st

CATEGORY_NAMES = {"EAU": "Eau", "VOIRIE": "Voirie / Routes", "DECHETS": "Déchets / Propreté",
                  "ECLAIRAGE": "Éclairage public", "TRANSPORT": "Transport / Mobilité"}
CATEGORY_COLORS = {"EAU": "#326779", "VOIRIE": "#74869d", "DECHETS": "#628884",
                   "ECLAIRAGE": "#9c885f", "TRANSPORT": "#64746b"}
PRIORITY_COLORS = {"Faible": "#81939b", "Moyenne": "#397a72", "Élevée": "#b18133", "Critique": "#ad4a4a"}
PRIORITY_CLASSES = {"Faible": "low", "Moyenne": "medium", "Élevée": "high", "Critique": "critical"}
DEMO_TEXT = "Données synthétiques de démonstration — elles ne représentent pas la situation réelle du territoire."

def html(value):
    st.markdown(value, unsafe_allow_html=True)

def apply_styles():
    html('<style>' + (Path(__file__).resolve().parents[1] / 'assets/style.css').read_text(encoding='utf-8-sig') + '</style>')

def demo_notice():
    html(f'<div class="tp-notice" role="note">{DEMO_TEXT}</div>')

def is_rtl(text):
    for char in text:
        direction = unicodedata.bidirectional(char)
        if direction in {"R", "AL"}:
            return True
        if direction == "L":
            return False
    return False

def quote(text, zone=None):
    zone_html = f'<div class="tp-zone">Zone · <bdi>{escape(zone)}</bdi></div>' if zone is not None else ''
    html(f'<div class="tp-report"><p dir="auto">{escape(text)}</p>{zone_html}</div>')

def example_text(text):
    html(f'<p class="tp-example-text" dir="auto">{escape(text)}</p>')

def analysis_cards(result):
    priority = result['priority']['level']
    items = [("Catégorie proposée", CATEGORY_NAMES[result['category']], ''),
             ("Confiance du modèle", f"{result['confidence']:.0%}", ''),
             ("Priorité suggérée", priority, 'tp-priority-' + PRIORITY_CLASSES[priority])]
    content = ''.join(f'<div class="tp-stat"><div class="tp-stat-label">{escape(label)}</div>'
                      f'<div class="tp-stat-value {style}">{escape(value)}</div></div>' for label,value,style in items)
    html('<div class="tp-stats" role="group" aria-label="Résultat de l’analyse">' + content + '</div>')

def route_panel(service):
    display_service = service.removesuffix(' – démonstration')
    html(f'<div class="tp-panel tp-route"><span class="tp-small">Routage recommandé</span>'
         f'<strong>{escape(display_service)}</strong><span class="tp-badge">Démonstration</span></div>')
    st.caption("Le routage présenté est une simulation. Une version réelle nécessiterait une intégration avec les organismes compétents.")

def priority_details(result):
    reasons = [re.sub(r'\s*\(\+\d+\)', '', item.strip()) for item in result['priority']['reason'].split(';')]
    bullets = ''.join('<li>' + escape(item[:1].upper() + item[1:]) + '</li>' for item in reasons)
    days = result['details']['duration_days']
    duration = 'non détectée' if days is None else f'{days} ' + ('jour' if days == 1 else 'jours')
    contexts = ', '.join(result['details']['contexts']) or 'non détecté'
    html(f'<div class="tp-detail-grid"><section class="tp-panel"><h3>Pourquoi cette priorité ?</h3><ul>{bullets}</ul>'
         f'<p>Score de règles : <strong>{int(result["priority"]["score"])}</strong></p>'
         '<p class="tp-small">Proposition à valider par un humain.</p></section>'
         f'<section class="tp-panel"><h3>Informations extraites</h3><p>Durée : {escape(duration)}</p>'
         f'<p>Contexte : {escape(contexts)}</p></section></div>')

def similarity_message(count):
    if count == 0:
        return 'Aucun signalement suffisamment similaire détecté dans cette zone.'
    if count == 1:
        return 'Un signalement similaire détecté dans cette zone.'
    return f'{count} signalements similaires détectés dans cette zone.'

def style_figure(figure):
    figure.update_layout(template='plotly_white', font=dict(family='Segoe UI, Tahoma, Arial, sans-serif', size=12, color='#193b45'),
                         paper_bgcolor='#ffffff', plot_bgcolor='#ffffff', height=325,
                         margin=dict(l=12, r=18, t=22, b=20), hoverlabel=dict(font_size=13),
                         legend=dict(orientation='h', title_text=''), bargap=.35)
    figure.update_xaxes(showgrid=True, gridcolor='#eef2f4', zeroline=False, automargin=True)
    figure.update_yaxes(zeroline=False, automargin=True)
    return figure

def chart(title, figure, key):
    st.markdown('#### ' + title)
    st.plotly_chart(style_figure(figure), width='stretch', key=key,
                    config={'displaylogo': False, 'scrollZoom': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                            'toImageButtonOptions': {'filename': 'tazapulse-demo'}})

def insights(reports, incidents):
    if reports.empty:
        return []
    counts = reports.predicted_category.value_counts()
    leaders = counts[counts == counts.max()]
    if len(leaders) == 1:
        lead = f'La catégorie « {CATEGORY_NAMES[leaders.index[0]]} » est la plus fréquente dans la sélection ({int(leaders.iloc[0])} signalements).'
    else:
        lead = f'{len(leaders)} catégories sont à égalité en tête, avec {int(leaders.iloc[0])} signalements chacune.'
    category = leaders.index[0]
    zones = reports.loc[reports.predicted_category == category, 'zone'].value_counts()
    zone_names = zones[zones == zones.max()].index.tolist()
    names = ' et '.join([', '.join(zone_names[:-1]), zone_names[-1]]) if len(zone_names) > 1 else zone_names[0]
    location = f'Pour « {CATEGORY_NAMES[category]} », {names} ' + ('concentrent' if len(zone_names)>1 else 'concentre') + f' le plus de signalements ({int(zones.max())} par zone citée).'
    groups = int((incidents['count'] >= 2).sum())
    grouping = ('Aucun groupe de plusieurs signalements similaires n’apparaît dans cette sélection.' if groups == 0 else
                ('Un groupe de signalements peut être examiné comme un incident potentiel commun.' if groups == 1 else
                 f'{groups} groupes de signalements peuvent être examinés comme des incidents potentiels communs.'))
    return [lead, location, grouping]
