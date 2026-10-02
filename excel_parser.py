import os
import pandas as pd

def load_students(file_path=None):
    """
    يقوم بقراءة ملف الإكسيل بذكاء وتحديد أعمدة الأسماء والصفوف
    حتى لو كانت هناك أعمدة فارغة في البداية.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if file_path is None:
        file_path = os.path.join(base_dir, "students.xlsx")

    if not os.path.exists(file_path):
        # البحث عن أي ملف إكسيل بديل في مجلد المشروع
        files = [os.path.join(base_dir, f) for f in os.listdir(base_dir) if f.endswith(".xlsx") and not f.startswith("~$")]
        if files:
            file_path = files[0]
        else:
            return [], []

    try:
        # قراءة أول 20 صف لمعاينة مكان الهيدر (العناوين)
        preview_df = pd.read_excel(file_path, header=None, nrows=20)
        
        header_row_idx = 0
        name_col_idx = None
        class_col_idx = None

        # البحث عن الصف الذي يحتوي على الكلمات المفتاحية
        for r_idx, row in preview_df.iterrows():
            row_str = [str(val).strip().lower() for val in row.values]
            for c_idx, val in enumerate(row_str):
                if any(kw in val for kw in ["الاسم", "اسم", "name"]):
                    if name_col_idx is None:
                        name_col_idx = c_idx
                        header_row_idx = r_idx
                if any(kw in val for kw in ["الصف", "فصل", "class"]):
                    if class_col_idx is None:
                        class_col_idx = c_idx
                        header_row_idx = r_idx

        # لو ملقاش عناوين صريحة، يبحث عن الأسطر التي بها نصوص بدلاً من NaN
        df = pd.read_excel(file_path, header=None)

        if name_col_idx is None or class_col_idx is None:
            # افتراض تتابعي استناداً لنتائج المعاينة الشائعة
            for col in df.columns:
                col_data = df[col].dropna().astype(str).str.strip()
                if name_col_idx is None and any(len(x) > 4 for x in col_data):
                    name_col_idx = col
                elif name_col_idx is not None and class_col_idx is None and col != name_col_idx:
                    class_col_idx = col

        # لو مفيش غير عمود اسم واحد فقط
        if name_col_idx is None:
            name_col_idx = 1 if 1 in df.columns else 0
        if class_col_idx is None:
            class_col_idx = name_col_idx + 1 if (name_col_idx + 1) in df.columns else name_col_idx

        # جلب البيانات بدءاً من الصف التالي للهيدر
        data_rows = df.iloc[header_row_idx + 1:].copy()

        students = []
        unique_classes = set()

        id_counter = 1
        for _, row in data_rows.iterrows():
            name_val = row.get(name_col_idx)
            class_val = row.get(class_col_idx)

            if pd.isna(name_val):
                continue

            name_str = str(name_val).strip()
            # استبعاد صفوف العناوين المكررة أو الأرقام المتسلسلة
            if not name_str or name_str.lower() in ["name", "الاسم", "اسم الطالب", "م"]:
                continue

            class_str = str(class_val).strip() if not pd.isna(class_val) else "عام"
            if class_str.lower() in ["class", "الصف", "الصف / الفصل", "nan"]:
                class_str = "عام"

            students.append({
                "id": id_counter,
                "name": name_str,
                "class": class_str
            })
            unique_classes.add(class_str)
            id_counter += 1

        sorted_classes = sorted(list(unique_classes))
        return students, sorted_classes

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return [], []

if __name__ == "__main__":
    students, classes = load_students()
    print(f"Total Loaded Students: {len(students)}")
    print(f"Classes: {classes}")
    if students:
        print("Sample:", students[:3])
