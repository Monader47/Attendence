import os
import io
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def get_arabic_font():
    """
    البحث عن خط عربي متاح في نظام ويندوز وتسجيله في ReportLab
    """
    possible_fonts = [
        ("ArabicFont", r"C:\Windows\Fonts\arial.ttf"),
        ("ArabicFont", r"C:\Windows\Fonts\tahoma.ttf"),
        ("ArabicFont", r"C:\Windows\Fonts\calibri.ttf"),
        ("ArabicFont", r"C:\Windows\Fonts\seguiemj.ttf"),
    ]
    
    font_name = "Helvetica"
    for name, path in possible_fonts:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                font_name = name
                break
            except Exception as e:
                continue
    return font_name

def ar(text):
    """
    إعادة تشكيل وحساب اتجاه النص العربي من اليمين لليسار
    """
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    bidi_text = get_display(reshaped_text)
    return bidi_text

def generate_pdf_report(attendance_list, output_target="Daily_Attendance_Report.pdf", date_str=None):
    """
    إنشاء ملف PDF مخصص لمدرسة الهرم للتربية الفكرية يقتصر فقط على الطلاب الحاضرين اليوم.
    يدعم تمرير اسم ملف أو BytesIO للتحميل المباشر دون مشاكل القفل على ويندوز.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    font_name = get_arabic_font()
    
    # التحقق مما إذا كان الهدف هو BytesIO أم اسم ملف
    is_bytes_io = isinstance(output_target, io.BytesIO)

    doc = SimpleDocTemplate(
        output_target,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # أنماط النصوص العربية
    title_style = ParagraphStyle(
        name='ArabicTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#1e3d59")
    )

    school_style = ParagraphStyle(
        name='ArabicSchool',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=13,
        leading=17,
        alignment=1,
        textColor=colors.HexColor("#2b580c")
    )

    subtitle_style = ParagraphStyle(
        name='ArabicSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#4a4a4a")
    )

    cell_style = ParagraphStyle(
        name='ArabicCell',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=1
    )

    cell_header_style = ParagraphStyle(
        name='ArabicCellHeader',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.white
    )

    # الترويسة الرئيسية
    elements.append(Paragraph(ar("مدرسة الهرم للتربية الفكرية"), school_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(ar("كشف الحضور اليومي للطلاب الحاضرين"), title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(ar(f"تاريخ اليوم: {date_str}"), subtitle_style))
    elements.append(Spacer(1, 10))

    # التصفية لاختيار الطلاب الحاضرين فقط
    total_students = len(attendance_list)
    present_students = [s for s in attendance_list if s.get("status") == "حاضر"]
    present_count = len(present_students)
    absent_count = total_students - present_count
    attendance_rate = round((present_count / total_students * 100), 1) if total_students > 0 else 0

    # جدول الإحصائيات الموجز
    stats_data = [
        [
            Paragraph(ar(f"نسبة الحضور: {attendance_rate}%"), cell_style),
            Paragraph(ar(f"عدد الغائبين: {absent_count}"), cell_style),
            Paragraph(ar(f"عدد الحاضرين: {present_count}"), cell_style),
            Paragraph(ar(f"إجمالي الطلاب: {total_students}"), cell_style)
        ]
    ]
    stats_table = Table(stats_data, colWidths=[130, 130, 130, 130])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f4f8")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 15))

    if not present_students:
        empty_style = ParagraphStyle(
            name='ArabicEmpty',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            leading=16,
            alignment=1,
            textColor=colors.HexColor("#e74c3c")
        )
        elements.append(Paragraph(ar("تنبيه: لا يوجد أي طلاب مسجلين كـ 'حاضر' حتى الآن اليوم."), empty_style))
        doc.build(elements)
        if is_bytes_io:
            output_target.seek(0)
        return output_target

    # جدول الطلاب الحاضرين فقط (الأعمدة RTL: ملاحظات | الصف / الفصل | اسم الطالب | م)
    table_data = [
        [
            Paragraph(ar("ملاحظات"), cell_header_style),
            Paragraph(ar("الصف / الفصل"), cell_header_style),
            Paragraph(ar("اسم الطالب الحاضر"), cell_header_style),
            Paragraph(ar("م"), cell_header_style)
        ]
    ]

    # تجميع الحاضرين بحسب الصفوف
    grouped = {}
    for student in present_students:
        c_name = student.get("class", "عام")
        if c_name not in grouped:
            grouped[c_name] = []
        grouped[c_name].append(student)

    counter = 1
    class_row_indices = []

    for class_name, students in grouped.items():
        # صف تقسيم الصف
        class_row_idx = len(table_data)
        class_row_indices.append(class_row_idx)
        
        table_data.append([
            Paragraph(ar("---"), cell_style),
            Paragraph(ar(f"الصف: {class_name}"), cell_style),
            Paragraph(ar(f"عدد الحاضرين في هذا الصف: {len(students)}"), cell_style),
            Paragraph(ar("#"), cell_style)
        ])
        
        for student in students:
            table_data.append([
                Paragraph(ar(student.get("notes", "")), cell_style),
                Paragraph(ar(student.get("class", "")), cell_style),
                Paragraph(ar(student.get("name", "")), cell_style),
                Paragraph(ar(str(counter)), cell_style)
            ])
            counter += 1

    t = Table(table_data, colWidths=[120, 130, 230, 40])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3d59")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))

    # تظليل صفوف أسماء الفصول باللون الأزرق الفاتح المميز
    for r_idx in class_row_indices:
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor("#e2e8f0")),
            ('FONTSTYLE', (0, r_idx), (-1, r_idx), 'BOLD')
        ]))

    elements.append(t)
    doc.build(elements)
    
    if is_bytes_io:
        output_target.seek(0)
    return output_target

if __name__ == "__main__":
    sample_data = [
        {"name": "احمد محمد احمد زكى", "class": "تهيئة ثان أ", "status": "حاضر", "notes": ""},
        {"name": "ادم عربي ابراهيم عبود", "class": "تهيئة ثان أ", "status": "غائب", "notes": "بعذر"},
        {"name": "مالك محمود عاطف رزق", "class": "تهيئة ثان ب", "status": "حاضر", "notes": ""}
    ]
    buf = io.BytesIO()
    generate_pdf_report(sample_data, buf)
    print(f"Generated PDF BytesIO successfully: {len(buf.getvalue())} bytes")
