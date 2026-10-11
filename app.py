import os
from html import escape
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from src.utils import ZONES
from src.classifier import load_model
from src.analysis import analyze
from src.storage import read_reports, save_report
from src.seed_data import ensure_demo, DEMO_EXAMPLES
from src.similarity import group_incidents, SIMILARITY_THRESHOLD
from src.priority import LEVELS
from src import ui

st.set_page_config(page_title="TazaPulse AI · Intelligence territoriale", page_icon="◉",
                   layout="wide", initial_sidebar_state="expanded")
ui.apply_styles()

@st.cache_resource
def resources():
    return load_model()

def navigate(page):
    st.session_state['navigation'] = page

def clear_analysis():
    for key in ['analysis', 'saved', 'submission_id']:
        st.session_state.pop(key, None)

def use_example(text):
    st.session_state['report_text'] = text
    clear_analysis()

# Conserve le brouillon lors de la navigation entre les pages.
st.session_state['report_text'] = st.session_state.get('report_text', '')
with st.sidebar:
    ui.html('<div class="tp-brand"><span class="tp-mark" aria-hidden="true">TP</span>'
            '<div><strong>TAZAPULSE AI</strong><small>INTELLIGENCE TERRITORIALE</small></div></div>')
    page = st.radio('Navigation', ['Accueil', 'Signaler un problème', 'Analyse IA', 'Dashboard territorial', 'À propos'],
                    key='navigation', label_visibility='collapsed')
    ui.html('<div class="tp-sidebar-note"><strong>SYNTHETIC / DEMO DATA</strong>'
            '<p>Prototype local • 5 catégories • 3 langues</p>'
            '<p>Aucune connexion aux administrations. La décision finale appartient à un humain.</p></div>')

try:
    if not os.environ.get('TAZAPULSE_REPORTS_PATH'):
        ensure_demo()
    with st.spinner('Préparation du modèle local…'):
        vectorizer, classifier = resources()
    reports = read_reports()
except Exception as exc:
    st.error(f'Le prototype ne peut pas charger ses données : {exc}')
    st.info('Vérifiez les droits d’écriture, puis lancez : python src/train_model.py')
    st.stop()

def display_analysis(standalone=False):
    if standalone:
        st.title('Votre signalement, structuré')
    else:
        st.subheader('Votre signalement, structuré')
    result = st.session_state.get('analysis')
    if result is None:
        st.info('Décrivez un problème pour obtenir une catégorie, une priorité suggérée et un routage recommandé.')
        st.button('Signaler un problème', type='primary', on_click=navigate, args=('Signaler un problème',), key='analysis_start')
        return
    ui.quote(result['text'], result['zone'])
    ui.analysis_cards(result)
    st.caption('La confiance est indicative : elle provient d’un modèle entraîné sur un petit corpus synthétique.')
    if result['needs_review']:
        st.warning('Confiance faible ou vocabulaire inconnu : la catégorie proposée doit être vérifiée par un humain.')
    ui.html('<p>' + escape(result['summary']) + '</p>')
    saved = st.session_state.get('saved')
    if not saved:
        ui.route_panel(result['service'])
    ui.priority_details(result)
    st.markdown('#### Rapprochements possibles')
    st.write(ui.similarity_message(result['similar_count']))
    st.caption('Même catégorie, même zone et similarité textuelle au-dessus du seuil défini. Le signalement analysé est exclu du décompte.')
    if result['similar_count']:
        with st.expander('Voir les signalements similaires'):
            matches = result['similar_reports'][['report_id', 'text', 'zone', 'similarity']].copy()
            matches['similarity'] = matches['similarity'].map(lambda score: f'{score:.0%}')
            st.dataframe(matches.rename(columns={'report_id':'Identifiant', 'text':'Signalement', 'zone':'Zone', 'similarity':'Similarité textuelle'}), hide_index=True, width='stretch')
    if saved:
        st.success(f"✓ Signalement enregistré dans le prototype\n\nIdentifiant\n\n**{saved['report_id']}**")
        ui.route_panel(saved['service'])
        st.caption('Dans une version déployée, ce dossier pourrait être transmis après intégration institutionnelle.')
        st.button('Voir le dashboard territorial', on_click=navigate, args=('Dashboard territorial',), key='saved_dashboard')
    else:
        st.caption('La confirmation enregistre ce signalement localement dans le prototype.')
        if st.button('Confirmer le signalement', type='primary', key='confirm'):
            try:
                fresh = analyze(result['text'], result['zone'], read_reports(), vectorizer, classifier)
                saved = save_report(fresh, st.session_state['submission_id'])
                st.session_state['analysis'] = fresh
                st.session_state['saved'] = saved
                st.rerun()
            except (ValueError, OSError) as exc:
                st.error(f'Enregistrement impossible : {exc}')

if page == 'Accueil':
    ui.html('<section class="tp-hero"><div class="tp-eyebrow">PROTOTYPE · TAZA INNOVATION AI CHALLENGE 2026</div>'
            '<h1>TAZAPULSE AI</h1><p class="tp-subtitle">De la voix citoyenne à l’intelligence territoriale</p>'
            '<p class="tp-arabic" dir="rtl" lang="ar">صوتك نبض منطقتك</p>'
            '<p>Décrivez un problème. TazaPulse le structure pour rendre les besoins du territoire plus lisibles.</p></section>')
    st.button('Signaler un problème', type='primary', key='home_start', on_click=navigate, args=('Signaler un problème',))
    with st.container(key='home_kpis'):
        a, b, c = st.columns(3)
        a.metric('Signalements de démonstration', len(reports))
        b.metric('Catégories', 5)
        c.metric('Langues', 3)
    st.subheader('Du signalement à une vue du territoire')
    for column, number, title, body in zip(st.columns(3), ['01', '02', '03'], ['Décrire', 'Structurer', 'Comprendre'],
        ['Le citoyen décrit librement son problème.', 'L’IA propose une catégorie, une priorité et un routage.',
         'Les signalements alimentent des indicateurs territoriaux.']):
        with column:
            ui.html(f'<div class="tp-step"><b><span class="tp-step-number">{number}</span> {title}</b><p>{body}</p></div>')
    ui.demo_notice()

elif page == 'Signaler un problème':
    st.title('Signaler un problème')
    st.write('Décrivez simplement la situation. Vous n’avez pas besoin de connaître le service compétent.')
    with st.expander('Essayer un exemple de démonstration'):
        st.caption('Un clic remplit le champ. Vous choisissez ensuite quand lancer l’analyse.')
        with st.container(key='examples'):
            for start in range(0, len(DEMO_EXAMPLES), 3):
                columns = st.columns(3)
                for offset, (sample, category) in enumerate(DEMO_EXAMPLES[start:start+3]):
                    index = start + offset
                    with columns[offset]:
                        with st.container(border=True):
                            language = 'Darija' if ui.is_rtl(sample) else 'Français'
                            st.button(f'{ui.CATEGORY_NAMES[category]} · {language}', key=f'example_{index}',
                                      width='stretch', on_click=use_example, args=(sample,))
                            ui.example_text(sample)
    with st.form('citizen_form'):
        zone_choice = st.selectbox('Zone / quartier / douar', ZONES + ['Autre zone (démonstration)'], key='zone_choice')
        custom_zone = st.text_input('Précisez la zone si vous avez choisi « Autre zone »', max_chars=100,
                                    placeholder='Nom du quartier ou du douar de démonstration')
        input_key = 'report_input_rtl' if ui.is_rtl(st.session_state['report_text']) else 'report_input_ltr'
        with st.container(key=input_key):
            text = st.text_area('Texte du signalement', height=145, max_chars=3000,
                                placeholder='Décrivez le problème avec vos mots…', key='report_text')
        ui.html('<p class="tp-small">Darija • <span dir="rtl" lang="ar">العربية</span> • Français</p>')
        submitted = st.form_submit_button('Analyser mon signalement', type='primary')
        st.caption('Démonstration uniquement. Évitez les renseignements personnels.')
    if submitted:
        clear_analysis()
        zone = custom_zone if zone_choice == 'Autre zone (démonstration)' else zone_choice
        try:
            st.session_state['analysis'] = analyze(text, zone, reports, vectorizer, classifier)
            st.session_state['submission_id'] = str(uuid4())
        except ValueError as exc:
            st.warning(str(exc))
    if st.session_state.get('analysis'):
        st.divider()
        display_analysis()

elif page == 'Analyse IA':
    display_analysis(standalone=True)

elif page == 'Dashboard territorial':
    st.title('Dashboard territorial')
    st.write('Vue synthétique des signalements de démonstration.')
    ui.demo_notice()
    with st.container(key='dashboard_filters'):
        left, right = st.columns(2)
        selected_zones = left.multiselect('Zone', sorted(reports.zone.unique()), placeholder='Toutes les zones')
        selected_categories = right.multiselect('Catégorie', list(ui.CATEGORY_NAMES),
                                                 format_func=ui.CATEGORY_NAMES.get, placeholder='Toutes les catégories')
        st.button('Actualiser les données')
    filtered = reports.copy()
    if selected_zones:
        filtered = filtered[filtered.zone.isin(selected_zones)]
    if selected_categories:
        filtered = filtered[filtered.predicted_category.isin(selected_categories)]
    incidents, assignments = group_incidents(filtered, vectorizer)
    with st.container(key='dashboard_kpis'):
        cards = st.columns(4)
        cards[0].metric('Total des signalements', len(filtered))
        cards[1].metric('Incidents potentiels regroupés', int((incidents['count'] >= 2).sum()))
        cards[2].metric('Zones concernées', filtered.zone.nunique())
        cards[3].metric('Priorités élevées / critiques', int(filtered.priority.isin(['Élevée', 'Critique']).sum()))
    st.caption('Un incident regroupé contient au moins deux signalements. Les filtres s’appliquent à toute la page.')
    if filtered.empty:
        st.info('Aucun signalement ne correspond à cette sélection.')
    else:
        category_counts = filtered.predicted_category.value_counts().rename_axis('Code').reset_index(name='Signalements')
        category_counts['Catégorie'] = category_counts.Code.map(ui.CATEGORY_NAMES)
        category_figure = px.bar(category_counts, x='Signalements', y='Catégorie', orientation='h', color='Catégorie',
                                 color_discrete_map={ui.CATEGORY_NAMES[k]:v for k,v in ui.CATEGORY_COLORS.items()})
        category_figure.update_layout(showlegend=False, yaxis_title='')
        category_figure.update_yaxes(categoryorder='total ascending')
        category_figure.update_xaxes(dtick=1)
        zones = filtered.zone.value_counts().rename_axis('Zone').reset_index(name='Signalements')
        zone_figure = px.bar(zones, x='Signalements', y='Zone', orientation='h', color_discrete_sequence=['#628884'])
        zone_figure.update_layout(yaxis_title='')
        zone_figure.update_yaxes(categoryorder='total ascending')
        zone_figure.update_xaxes(dtick=1)
        left, right = st.columns(2)
        with left:
            ui.chart('Signalements par catégorie', category_figure, 'chart_categories')
        with right:
            ui.chart('Signalements par zone', zone_figure, 'chart_zones')
        priority_counts = filtered.priority.value_counts().reindex(LEVELS, fill_value=0).rename_axis('Priorité').reset_index(name='Signalements')
        priority_figure = px.bar(priority_counts, x='Priorité', y='Signalements', color='Priorité', color_discrete_map=ui.PRIORITY_COLORS)
        priority_figure.update_layout(showlegend=False, xaxis_title='')
        priority_figure.update_yaxes(dtick=max(1, (int(priority_counts.Signalements.max()) + 5) // 6))
        left, right = st.columns(2)
        with left:
            ui.chart('Priorités suggérées', priority_figure, 'chart_priorities')
        daily = pd.to_datetime(filtered.timestamp, format='ISO8601', utc=True).dt.floor('D').value_counts().sort_index()
        with right:
            if len(daily) >= 2:
                daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max(), freq='D'), fill_value=0)
                timeline = daily.rename_axis('Date').reset_index(name='Signalements')
                daily_figure = px.line(timeline, x='Date', y='Signalements', markers=True, color_discrete_sequence=['#326779'])
                daily_figure.update_xaxes(tickformat='%d/%m', title='Date · UTC')
                daily_figure.update_yaxes(dtick=1)
                daily_figure.update_traces(hovertemplate='%{x|%d/%m/%Y}<br>Signalements : %{y}<extra></extra>')
                ui.chart('Évolution quotidienne', daily_figure, 'chart_daily')
            else:
                st.markdown('#### Évolution quotidienne')
                st.info('L’évolution apparaît lorsque les signalements couvrent au moins deux dates.')
        st.subheader('Territorial Insights')
        st.caption('Observations calculées à partir des données de démonstration sélectionnées.')
        for observation in ui.insights(filtered, incidents):
            ui.html('<p>' + escape(observation) + '</p>')
        st.caption('Ces observations sont indicatives et nécessitent une validation humaine.')
        st.subheader('Incidents les plus signalés')
        incident_view = incidents.copy()
        incident_view['category'] = incident_view.category.map(ui.CATEGORY_NAMES)
        st.dataframe(incident_view.rename(columns={'incident_id':'Incident', 'zone':'Zone', 'category':'Catégorie',
                         'count':'Signalements', 'priority':'Priorité maximale', 'example':'Exemple'}), hide_index=True, width='stretch')
        with st.expander('Registre des signalements confirmés'):
            registry = filtered.drop(columns='submission_id').copy()
            registry['incident_id'] = registry.report_id.map(assignments)
            registry['predicted_category'] = registry.predicted_category.map(ui.CATEGORY_NAMES)
            registry['status'] = registry.status.map({'RECEIVED':'Enregistré', 'ROUTED_DEMO':'Routage simulé'}).fillna(registry.status)
            registry['data_source'] = registry.data_source.map({'SYNTHETIC / DEMO DATA':'Historique synthétique',
                                         'USER INPUT / DEMO ONLY':'Saisie de démonstration'}).fillna(registry.data_source)
            st.dataframe(registry.rename(columns={'report_id':'Identifiant', 'timestamp':'Date · UTC', 'text':'Signalement',
                'zone':'Zone', 'predicted_category':'Catégorie', 'priority':'Priorité suggérée', 'service':'Service de démonstration',
                'status':'Statut', 'data_source':'Source', 'incident_id':'Incident potentiel'}), hide_index=True, width='stretch')

else:
    st.title('À propos de TAZAPULSE AI')
    st.write('De la voix citoyenne à l’intelligence territoriale')
    left, right = st.columns(2)
    with left:
        st.subheader('Le problème')
        st.write('Les citoyens connaissent leur problème mais ne savent pas toujours comment le structurer ou vers quel service l’orienter.')
    with right:
        st.subheader('La solution')
        st.write('TazaPulse transforme un signalement libre en information structurée exploitable.')
    st.caption('Axes · Développement territorial · Inclusion')
    st.subheader('Composantes IA')
    st.write('Classification NLP avec TF-IDF et régression logistique ; similarité cosinus ; extraction simple d’informations ; priorisation assistée et routage intelligent.')
    with st.expander('Comprendre les propositions du système'):
        st.write('TF-IDF combine des groupes de mots (1–2) et de caractères (3–5). La régression logistique propose l’une des cinq catégories. La confiance affichée n’est pas calibrée sur des données réelles.')
        st.write(f'Les rapprochements exigent la même catégorie, la même zone et une similarité textuelle d’au moins {SIMILARITY_THRESHOLD:.0%}. Ils ne prouvent pas qu’il s’agit du même incident.')
        st.write('Score de priorité : danger +3 ; école, enfants ou soins +2 ; obstacle +1 ; durée d’au moins trois jours +2 ; un ou deux signalements similaires +1, au moins trois +2.')
        st.write('Faible : 0 ; Moyenne : 1–2 ; Élevée : 3–5 ; Critique : 6 et plus. Aucune catégorie n’est critique automatiquement.')
    st.subheader('Limites du prototype')
    st.markdown('- Données synthétiques et cinq catégories seulement.\n- Aucune connexion administrative ; routage simulé.\n- Validation avec de vraies données nécessaire.\n- Formulations inconnues, négations et rapprochements entre langues parfois mal interprétés.')
    st.caption('La décision finale appartient toujours à un humain.')
    st.subheader('Évolutions envisagées')
    st.write('Reconnaissance vocale, géolocalisation, photos, modèle NLP plus avancé et intégration institutionnelle. Ces fonctions ne sont pas intégrées au prototype.')
    ui.demo_notice()

