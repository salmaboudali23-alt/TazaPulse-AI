"""Corpus entièrement SYNTHETIC / DEMO DATA. Ne remplace jamais un fichier existant."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import ROOT, ZONES
from src.routing import route

# 30 formulations distinctes par catégorie : 10 darija, 10 arabe, 10 français.
CORPUS = {
"EAU": [
"الما تقطع لينا فالدار", "ما عندناش الما فالدوار", "الما ما جا من الصباح", "الروبيني ما كيخرج والو", "كاين تسرب ديال الما فالزنقة", "الما ضعيف بزاف فالحي", "الما جاي موسخ وريحتو خايبة", "القادوس ديال الما مكسور", "بغينا الما يرجع للديور", "الما كيتقطع كل نهار",
"انقطاع الماء عن المنازل منذ أمس", "لا تتوفر مياه الشرب في الحي", "تسرب المياه من قناة مكسورة", "ضعف ضغط الماء في الشبكة", "الماء غير صالح للشرب بسبب الرائحة", "انفجار أنبوب الماء قرب المنازل", "صنبور عمومي لا يعمل", "الماء مقطوع في القرية", "تلوث مياه الشرب في المنطقة", "نحتاج إلى إصلاح شبكة المياه",
"Coupure d'eau dans notre quartier", "Le robinet reste sec ce matin", "Une fuite sur le réseau d'eau potable", "La pression de l'eau est trop faible", "L'eau du robinet a une odeur inhabituelle", "Une canalisation d'eau est cassée", "Les maisons sont privées d'eau potable", "Nous subissons des coupures d'eau répétées", "L'alimentation en eau est interrompue", "La borne fontaine ne distribue plus d'eau"],
"VOIRIE": [
"الطريق خاسرة بزاف", "كاينة حفرة كبيرة وسط الزنقة", "الزنقة عامرة بالحفر", "الطريق تقطعات من الشتا", "القنطرة فيها تشققات", "الرصيف مهرس قدام الدار", "الطريق مسدودة بالحجر", "خاص يتصلح الزفت ديال الطريق", "كاينة حفرة قدام المدرسة", "الطريق ولات صعيبة على الطوموبيلات",
"الطريق متضررة وتحتاج إلى إصلاح", "حفرة عميقة في الشارع الرئيسي", "تشققات في الرصيف تعيق المشاة", "انهيار جزء من الطريق بعد المطر", "الحجارة تغلق الطريق المؤدية للقرية", "الجسر به تشققات واضحة", "الشارع مليء بالحفر الخطيرة", "تضرر الإسفلت أمام المدرسة", "انجراف التربة قطع المسلك", "الرصيف مكسور قرب السوق",
"La chaussée est très abîmée", "Un nid de poule se trouve devant l'école", "La route est dégradée sur plusieurs mètres", "Le trottoir est cassé près du marché", "Des pierres bloquent la route", "Le pont présente des fissures", "Un trou profond gêne les voitures", "La route s'est affaissée après la pluie", "Il faut réparer le revêtement de la chaussée", "La piste vers le village est impraticable"],
"DECHETS": [
"الزبل مجموع فالحي", "الزبالة بقات هنا بزاف", "الطراش عامر وما جا حتى حد يديه", "الزبل كيخرج ريحة خايبة", "كاينة كومة ديال الزبل حدا السوق", "خاص الزنقة تتنقى من الزبل", "ما دازش كاميو ديال الزبل", "الزنقة عامرة بالوسخ", "الزبالة حد المدرسة من ثلاثة ايام", "الزبل مرمي حدا الديور",
"تراكم النفايات في الحي منذ أيام", "حاويات القمامة ممتلئة", "لم تمر شاحنة جمع النفايات", "رائحة كريهة بسبب القمامة", "انتشار الأزبال بالقرب من السوق", "النفايات المنزلية لم تجمع", "نحتاج إلى تنظيف الشارع", "مخلفات متراكمة أمام المدرسة", "القمامة منتشرة على الرصيف", "حاوية النفايات تفيض منذ أسبوع",
"Les ordures s'accumulent près des maisons", "Les poubelles débordent depuis cinq jours", "Le camion de collecte ne passe plus", "Des déchets jonchent la rue", "Une odeur provient des tas d'ordures", "Le quartier a besoin de nettoyage", "Les bacs à déchets sont pleins", "Des ordures sont abandonnées près du marché", "La collecte des déchets est interrompue", "Les déchets ménagers restent devant l'école"],
"ECLAIRAGE": [
"المصباح ما خدامش فالزنقة", "الضو ديال الزنقة طافي", "المصابيح كاملين طافيين", "الزنقة ظلام فالليل", "البوطو ديال الضو طايح", "اللامبة ديال الشارع محروقة", "الضو العمومي كيشعل ويطفى", "المصابيح ما خدامينش حدا الدار", "السلك ديال ضو الزنقة خارج", "خاص يتصلح الضو فالشارع",
"مصابيح الإنارة العمومية معطلة", "الشارع مظلم في الليل", "عمود الإنارة متضرر", "انقطاع الإنارة عن الحي", "مصباح الشارع لا يشتغل", "أسلاك عمود الإنارة مكشوفة", "أضواء الشارع تنطفئ باستمرار", "الإنارة ضعيفة قرب المدرسة", "نحتاج إلى إصلاح مصابيح الشارع", "عمود الإضاءة مائل ويهدد المارة",
"Le lampadaire ne fonctionne plus", "L'éclairage public est en panne", "La rue reste dans le noir la nuit", "Un poteau d'éclairage est tombé", "Les lampes de la rue sont éteintes", "Un câble dépasse du lampadaire", "L'ampoule du réverbère est grillée", "Les lumières publiques clignotent", "L'éclairage près de l'école est insuffisant", "Plusieurs lampadaires sont défectueux"],
"TRANSPORT": [
"ما كاينش النقل من الدوار للمدينة", "الطوبيس ما جاش اليوم", "ما عندنا حتى وسيلة نقل", "الطوبيسات كيجيوا عامرين", "النقل المدرسي ما كاينش", "الطاكسيات ما كيوصلوش للدوار", "خاصنا طوبيس باش نمشيو للمدينة", "كنبقاو نتسناو النقل ساعات", "الطوبيس كيتعطل كل صباح", "محطة النقل بعيدة على السكان",
"لا تتوفر وسائل النقل إلى المدينة", "الحافلة تتأخر كثيرا", "غياب النقل المدرسي في القرية", "خط الحافلات لا يخدم المنطقة", "اكتظاظ حافلات النقل العمومي", "نحتاج إلى رحلات إضافية للحافلات", "محطة الحافلات بعيدة عن السكان", "انقطاع خدمة النقل بين القرية والمدينة", "سيارات الأجرة لا تصل إلى المنطقة", "انتظار طويل لوسيلة نقل",
"Aucun bus ne dessert notre village", "Le transport vers la ville est absent", "Les autobus sont toujours en retard", "Le ramassage scolaire n'est pas assuré", "Les bus sont surchargés le matin", "Il manque une liaison de transport rural", "Les taxis ne desservent pas cette zone", "L'arrêt de bus est trop éloigné", "Nous attendons le bus depuis deux heures", "La fréquence des transports est insuffisante"],
}

DEMO_EXAMPLES = [
    ("الزبل مجموع فالحي من خمسة أيام", "DECHETS"),
    ("الما مقطوع عندنا من البارح", "EAU"),
    ("كاينة حفرة كبيرة فالطريق قدام المدرسة", "VOIRIE"),
    ("المصابيح ما خدامينش فالزنقة", "ECLAIRAGE"),
    ("ما كاين حتى نقل من الدوار للمدينة", "TRANSPORT"),
    ("Les déchets sont accumulés dans le quartier depuis trois jours.", "DECHETS"),
    ("Il n’y a plus d’eau depuis hier.", "EAU"),
]

def ensure_training(path=None):
    path = Path(path or ROOT / "data/training_reports.csv")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["text", "label"])
            writer.writerows((text, label) for label, texts in CORPUS.items() for text in texts)
    return path

def ensure_demo(path=None):
    from src.storage import COLUMNS
    from src.priority import suggest_priority
    path = Path(path or ROOT / "data/demo_reports.csv")
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc)
    rows = []
    # 40 signalements historiques, cinq catégories, six zones, plusieurs dates.
    for i in range(40):
        category = list(CORPUS)[i % 5]
        group = i // 5
        zone = ZONES[(i % 5 + group // 3) % len(ZONES)]
        text = CORPUS[category][[0, 1, 7, 10, 11, 17, 20, 21][group]]
        rows.append(dict(zip(COLUMNS, [
            f"TZA-{i+1:04d}", (start + timedelta(hours=11*i)).isoformat(),
            text, zone, category, suggest_priority(text)["level"], route(category),
            "ROUTED_DEMO", f"seed-{i+1}", "SYNTHETIC / DEMO DATA",
        ])))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path

if __name__ == "__main__":
    print(ensure_training())
    print(ensure_demo())
